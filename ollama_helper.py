import requests

import common_functions as cf

class OllamaHelper:
    def __init__(self, ollama_home):
        self.err, self.ollama_home = cf.clean_url(ollama_home)

    def get_ollama_model_info(self, model):
        if cf.isNotBlank(self.err):
            return self.err, {}

        try:
            data = {
                "model": model,
                "verbose": False
                        }
            response = requests.post(f"{self.ollama_home}/api/show", json=data)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            return f"HTTP error occurred: {e}", {}
        except requests.exceptions.ConnectionError as e:
            return f"Connection error occurred: {e}", {}
        except requests.exceptions.RequestException as e:
            return f"Request error occurred: {e}", {}
    
        json = response.json()

        model_info = {}
        if 'license' in json:
            model_info['license'] = json['license'].splitlines()[0].strip()

        if 'details' in json:
            if 'family' in json['details']:
                model_info['family'] = json['details']['family']
            if 'format' in json['details']:
                model_info['format'] = json['details']['format']
            if 'parameter_size' in json['details']:
                model_info['parameter_size'] = json['details']['parameter_size']
            if 'quantization_level' in json['details']:
                model_info['quantization_level'] = json['details']['quantization_level']
        if 'model_info' in json:
            arch = None
            if 'general.architecture' in json['model_info']:
                arch = json['model_info']['general.architecture']
                model_info['architecture'] = arch
            if arch is not None and f"{arch}.context_length" in json['model_info']:
                model_info['context_length'] = json['model_info'][f"{arch}.context_length"]

        return "", model_info, json

    def get_all_ollama_models_and_infos(self):
        if cf.isNotBlank(self.err):
            return self.err, {}

        model_info = {}
        try:
            response = requests.get(f"{self.ollama_home}/api/tags")
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            return f"HTTP error occurred: {e}", model_info
        except requests.exceptions.ConnectionError as e:
            return f"Connection error occurred: {e}", model_info
        except requests.exceptions.RequestException as e:
            return f"Request error occurred: {e}", model_info

    # {"models":[{"name":"llama3.3:70b","model":"llama3.3:70b","modified_at":"2025...","size":42...,"digest":"a6...","details":{"parent_model":"","format":"gguf","family":"llama","families":["llama"],"parameter_size":"70.6B","quantization_level":"Q4_K_M"}}]}
        if 'models' not in response.json():
            return f"Ollama's response does not contain models", {}
        models = response.json()['models']
        for model in models:
            err, info, _ = self.get_ollama_model_info(model['model'])
            if cf.isNotBlank(err):
                return err, {}
            model_info[model['model']] = info

        return "", model_info

    def ollama_to_modelsjson(self, model_name, info):
        if cf.isNotBlank(self.err):
            return self.err, {}

        # INPUT: 'llama3.3:70b': {'license': 'LLAMA 3.3 COMMUNITY LICENSE AGREEMENT', 'family': 'llama', 'format': 'gguf', 'parameter_size': '70.6B', 'quantization_level': 'Q4_K_M', 'architecture': 'llama', 'context_length': 131072}
        # OUTPUT: 'llama3.3:70b': { "label": "[Ollama] Architecture: llama, Format: gguf, License: LLAMA 3.3 COMMUNITY LICENSE AGREEMENT, Family: llama, Parameter size: 70.6B, Quantization level: Q4_K_M", "max_token": 4096, "context_token": 131072, "data": "Ollama model","status": "active", "status_details": "", "capability": [], "meta": { "provider": "Ollama", "apiurl": f"{ollama_home}/v1/"}
        if 'license' not in info:
            info['license'] = 'Unknown'
        if 'family' not in info:
            info['family'] = 'Unknown'
        if 'format' not in info:
            info['format'] = 'Unknown'
        if 'parameter_size' not in info:
            info['parameter_size'] = 'Unknown'
        if 'quantization_level' not in info:
            info['quantization_level'] = 'Unknown'
        if 'architecture' not in info:
            info['architecture'] = 'Unknown'
        if 'context_length' not in info:
            info['context_length'] = 4096
        max_token = 16000 if info['context_length'] > 16000 else info['context_length']

        label = f"[Ollama] Architecture: {info['architecture']}, Format: {info['format']}, License: {info['license']}, Family: {info['family']}, Parameter size: {info['parameter_size']}, Quantization level: {info['quantization_level']}"

        return "", {
            "label": label,
            "max_token": max_token,
            "context_token": info['context_length'],
            "data": "Ollama model",
            "status": "active",
            "status_details": f"using Ollama: allowing vision and using a default value for max_token. See https://ollama.com/library/{model_name} for actual model capabilities.",
            "capability": ["vision"],
            "meta": {
                "provider": "Ollama",
                "apikey": "ollama",
                "apiurl": f"{self.ollama_home}/v1/"
            }
        }
    
