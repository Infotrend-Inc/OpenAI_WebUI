import requests

import common_functions as cf


class LiteLLMHelper:
    def __init__(self, litellm_url, litellm_apikey):
        self.err, self.litellm_url = cf.clean_url(litellm_url)
        self.litellm_apikey = litellm_apikey

    def get_all_litellm_models_and_infos(self):
        model_info = {}
        if cf.isNotBlank(self.err):
            return self.err, model_info
        try:
            response = requests.get(f"{self.litellm_url}/v1/model/info", headers={"accept": "application/json", "x-litellm-api-key": self.litellm_apikey})
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            return f"HTTP error occurred: {e}", model_info
        except requests.exceptions.ConnectionError as e:
            return f"Connection error occurred: {e}", model_info
        except requests.exceptions.RequestException as e:
            return f"Request error occurred: {e}", model_info

    
        # { "data": [
        #     {
        #       "model_name": "openrouter/meta-llama/llama-3-70b-instruct",
        #       "litellm_params": {
        #         [...]
        #         "model": "openrouter/meta-llama/llama-3-70b-instruct"
        #       },
        #       "model_info": {
        #         "max_tokens": 8192,
        #         "max_input_tokens": null,
        #         "max_output_tokens": null,
        #         "mode": "chat",
        #         "supports_system_messages": true,
        #         "supports_vision": true,
        #         "supports_web_search": true,
        #         [...]

        if 'data' not in response.json():
            return f"Litellm's response does not contain models", {}
        json = response.json()['data']

        model_info = {}

        for model in json:
            if 'model_name' in model:
                model_info[model['model_name']] = {}
            else:
                return f"Litellm's response does not contain model_name", {}
            if 'model_info' in model:
                if 'max_tokens' in model['model_info']:
                    model_info[model['model_name']]['max_tokens'] = model['model_info']['max_tokens']
                if 'max_input_tokens' in model['model_info'] and model['model_info']['max_input_tokens'] is not None:
                    model_info[model['model_name']]['max_input_tokens'] = model['model_info']['max_input_tokens']
                if 'max_output_tokens' in model['model_info'] and model['model_info']['max_output_tokens'] is not None:
                    model_info[model['model_name']]['max_output_tokens'] = model['model_info']['max_output_tokens']

                if 'mode' in model['model_info']:
                    model_info[model['model_name']]['mode'] = model['model_info']['mode']

                if 'supports_system_messages' in model['model_info']:
                    model_info[model['model_name']]['supports_system_messages'] = model['model_info']['supports_system_messages']

                if 'supports_vision' in model['model_info']:
                    model_info[model['model_name']]['supports_vision'] = model['model_info']['supports_vision']
                if 'supports_web_search' in model['model_info']:
                    model_info[model['model_name']]['supports_web_search'] = model['model_info']['supports_web_search']

        return "", model_info

    def litellm_to_modelsjson(self, model_name, info):
        if cf.isNotBlank(self.err):
            return self.err, {}

        xtra = []
        if 'max_tokens' not in info:
            info['max_tokens'] = 4096
        if 'max_input_tokens' not in info:
            info['max_input_tokens'] = info['max_tokens']
            xtra.append("max_input_tokens")
        if 'max_output_tokens' not in info:
            info['max_output_tokens'] = info['max_tokens']
            xtra.append("max_output_tokens")
        
        if 'mode' in info and info['mode'] != 'chat':
            info['mode'] = 'chat'
        if 'mode' not in info:
            info['mode'] = 'chat'
        
        capability = []
        if 'supports_vision' in info and info['supports_vision']:
            capability.append("vision")
        if 'supports_web_search' in info and info['supports_web_search']:
            capability.append("web_search")

        meta = {
                "provider": "LiteLLM",
                "apikey-env": "LITELLM_API_KEY",
                "apiurl": f"{self.litellm_url}"
            }

        if 'supports_system_messages' in info and info['supports_system_messages'] is False:
            meta['removed_roles'] = ["system"]

        label = f"[LiteLLM] Model: {model_name}"
        if len(xtra) > 0:
            label += " The following fields are missing in the response and were set to default values: "
            label += f"{', '.join(xtra)}"
            label += " (Ask your LiteLLM admin to set those values)"

        model_dict = {
            "label": label,
            "max_token": info['max_output_tokens'],
            "context_token": info['max_input_tokens'],
            "data": "LiteLLM model",
            "status": "active",
            "status_details": f"using LiteLLM",
            "capability": capability,
            "meta": meta
        }

#        print(model_dict)
    
        return "", model_dict
