import openai
from openai import OpenAI

import json

import os.path

import copy

import common_functions as cf


#####
# 20241206: Removed temperature and max_tokens from the function call, those are now passed within kwargs
def simpler_gpt_call(apikey, messages, model_engine, **kwargs):
    client = OpenAI(api_key=apikey)

    # beta models limitation: https://platform.openai.com/docs/guides/reasoning
    # o1 will may not provide an answer if the max_completion_tokens is lower than 2000

#    with open("msg.json", 'w') as f:
#        json.dump(messages, f, indent=4)

    # Generate a response (20231108: Fixed for new API version)
    try:
        response = client.chat.completions.create(
            model=model_engine,
            messages = messages,
            **kwargs
        )
    # using list from venv/lib/python3.11/site-packages/openai/_exceptions.py
    except openai.APIConnectionError as e:
        return(f"OpenAI API request failed to connect: {e}", "")
    except openai.AuthenticationError as e:
        return(f"OpenAI API request was not authorized: {e}", "")
    except openai.RateLimitError as e:
        return(f"OpenAI API request exceeded rate limit: {e}", "")
    except openai.APIError as e:
        return(f"OpenAI API returned an API Error: {e}", "")
    except openai.OpenAIError as e:
        return(f"OpenAI API request failed: {e}", "")

#    with open("response.txt", 'w') as f:
#        f.write(f"{response}")
    return "", response.choices[0].message.content

##########
class OAI_GPT:
    def __init__(self, apikey, base_save_location, username):
        print("---------- [INFO] In OAI_GPT __init__ ----------")

        if cf.isBlank(base_save_location):
            base_save_location = "savedir"
        if cf.isBlank(username):
            username = "test"

        self.apikey = apikey
        self.save_location = os.path.join(base_save_location, username, "gpt")
        err = cf.make_wdir_recursive(self.save_location)
        if cf.isNotBlank(err):
            cf.error_exit(err) # nothing else to do here
        self.last_runfile = os.path.join(self.save_location, "last_run.json")

        self.models = {}
        self.models_status = {}
        self.model_help = ""
        self.per_model_help = {}
        self.gpt_presets = {}
        self.gpt_presets_help = ""
        self.gpt_roles = {}
        self.gpt_roles_help = ""
        self.model_capability = {}
        self.beta_models = {}


#####
    def get_models(self):
        return self.models

    def get_models_status(self):
        return self.models_status

    def get_model_help(self):
        return self.model_help
    
    def get_model_capability(self):
        return self.model_capability

    def get_per_model_help(self):
        return self.per_model_help

    def get_gpt_presets(self):
        return self.gpt_presets

    def get_gpt_presets_help(self):
        return self.gpt_presets_help

    def get_gpt_roles(self):
        return self.gpt_roles

    def get_gpt_roles_help(self):
        return self.gpt_roles_help

    def get_save_location(self):
        return self.save_location

    def get_beta_models(self):
        return self.beta_models
    

#####
# https://platform.openai.com/docs/models/continuous-model-upgrades
    def set_parameters(self, models_list, av_models_list):
        models = {}
        models_status = {}
        model_help = ""

        warning = ""

        s_models_list = models_list.replace(",", " ").split()
        known_models = list(av_models_list.keys())
        for t_model in s_models_list:
            model = t_model.strip()
            if model in av_models_list:
                if av_models_list[model]["status"] == "deprecated":
                    warning += f"Model {model} is deprecated (" + av_models_list[model]["status_details"] + "), discarding it. "
                else:
                    models[model] = dict(av_models_list[model])
                    if cf.isNotBlank(models[model]["status_details"]):
                        models_status[model] = models[model]["status"] +" (" + models[model]["status_details"] + ")"
            else:
                return f"Unknown model: {model} | Known models: {known_models}", warning

        model_help = ""
        for key in models:
            per_model_help = f"{key} (" + models[key]["status"] + "):\n"
            per_model_help += models[key]["label"] + "\n"
            per_model_help += "[Data: " + models[key]["data"] + " | "
            per_model_help += "Tokens -- max: " + str(models[key]["max_token"]) + " / "
            per_model_help += "context: " + str(models[key]["context_token"]) + "]"
            if cf.isNotBlank(models[key]["capability"]):
                per_model_help += " | Capability: " + models[key]["capability"]
                self.model_capability[key] = models[key]["capability"]
            else:
                self.model_capability[key] = "None"
            if 'beta_model' in models[key]:
                self.beta_models[key] = models[key]['beta_model']
            else:
                self.beta_models[key] = False
            if cf.isNotBlank(models[key]["status_details"]):
                per_model_help += " NOTE: " + models[key]["status_details"]
            self.per_model_help[key] = per_model_help
            model_help += f"{per_model_help}\n\n"

        active_models = [x for x in av_models_list if av_models_list[x]["status"] == "active"]
        active_models_txt = ",".join(active_models)

        if len(models) == 0:
            return f"No models retained, unable to continue. Active models: {active_models_txt}", warning

        model_help += "For a list of available supported models, see https://github.com/Infotrend-Inc/OpenAI_WebUI\n\n"
        model_help += f"List of active models supported by this release: {active_models_txt}\n\n"

        self.models = models
        self.models_status = models_status
        self.model_help = model_help

        self.gpt_presets = {
            "None": {
                "pre": "",
                "post": "",
                "kwargs": {}
            },
            "Keywords": {
                "pre": "Extract keywords from this text: ",
                "post": "",
                "kwargs": {"top_p": 1.0, "frequency_penalty": 0.8, "presence_penalty": 0.0}
            },
            "Summarization": {
                "pre": "",
                "post": "Tl;dr",
                "kwargs": {"top_p": 1.0, "frequency_penalty": 0.0, "presence_penalty": 1}
            }
        }

        self.gpt_presets_help = "None: regular, no additonal parameters\n\nKeywords: Extract keywords from a block of text. At a lower temperature it picks keywords from the text. At a higher temperature it will generate related keywords which can be helpful for creating search indexes.\n\nSummarization: Summarize text."

        self.gpt_roles =  {
            'user': 'help instruct the assistant',
            'system': 'helps set the behavior of the assistant (ex: "You are a helpful assistant. You also like to speak in the words of Shakespeare. Incorporate that into your responses.")',
            'assistant': 'helps set the past conversations. This is relevant when you had a chat that went over the maximum number of tokens and need to start a new one: give the chat history some fresh context'
        } 

        self.gpt_roles_help = ""
        for key in self.gpt_roles:
            self.gpt_roles_help += key + ":\n" + self.gpt_roles[key] + "\n\n"

        return "", warning

#####
    def get_rf_role_prompt_response(self, run_file):
        role = ""
        prompt = ""
        response = ""
        
        run_json = cf.get_run_file(run_file)
        if 'role' in run_json:
            role = run_json['role']
        if 'prompt' in run_json:
            prompt = run_json['prompt']
        if 'response' in run_json:
            response = run_json['response']

        return (role, prompt, response)


#####
    def get_dest_dir(self):
        return os.path.join(self.save_location, cf.get_timeUTC())


#####
    def format_rpr(self, role, text):
        return (f"\n\n--------------------------\n\n -- role: {role}\n\n -- text: {text}\n\n")

#####
    def get_chat_history_core(self, run_file):
        # return: array of multple set of 5 elements: err, len(messages), role, prompt, response
        err = cf.check_file_r(run_file)
        if cf.isNotBlank(err):
            return f"run file {run_file} issue ({err}), truncating chat history", []

        run_json = cf.get_run_file(run_file)
        if 'messages' not in run_json:
            return f"run file {run_file} does not contain messages", []

        return "", run_json['messages']


    def get_chat_history(self, run_file):
        err, dict_array = self.get_chat_history_core(run_file)
        if cf.isNotBlank(err):
            return err
        
        txt = ""
        # process each dict in the array
        if len(dict_array) == 0:
            return "No messages in chat history"
        for msg in dict_array:
            if 'oaiwui_skip' in msg:
                continue
            if 'content' not in msg:
                continue
            if 'type' not in msg['content'][0]:
                continue

            if msg['content'][0]['type'] == 'text':
                txt += self.format_rpr(msg['role'], msg['content'][0]['text'])

        return(txt)


#####
    def chatgpt_it(self, model_engine, prompt, max_tokens, temperature, clear_chat, role, msg_extra=None, **kwargs):
        dest_dir = self.get_dest_dir()
        err = cf.make_wdir_recursive(dest_dir)
        if cf.isNotBlank(err):
            return f"While checking {dest_dir}: {err}", ""
        slug = os.path.basename(dest_dir)

        err = cf.check_existing_dir_w(dest_dir)
        if cf.isNotBlank(err):
            return f"While checking {dest_dir}: {err}", ""

        messages = []
        if msg_extra is not None:
            for msg in msg_extra:
                msg_copy = copy.deepcopy(msg)
                if 'oaiwui_skip' in msg_copy:
                    msg_copy['oaiwui_skip'] = slug
                messages.append(msg_copy)
#                print(msg_copy['content'][0]['type'])

        if clear_chat is False:
            # Obtain previous messages
            if cf.isNotBlank(self.last_runfile):
                run_file = ""
                if cf.check_file_r(self.last_runfile) == "":
                    tmp = cf.read_json(self.last_runfile)
                    if 'last_runfile' in tmp:
                        run_file = tmp['last_runfile']
                if cf.isNotBlank(run_file): # We can only load previous messages if the file exists
                    if cf.check_file_r(run_file) == "":
                        old_run_json = cf.get_run_file(run_file)
                        if 'messages' in old_run_json:
                            for msg in old_run_json['messages']:
                                messages.append(msg)

        to_add = { 'role': role, 'content': [ {'type': 'text', 'text': prompt} ] }
        messages.append(to_add)

        clean_messages = []
        stored_messages = []
        msg_count = 0
        for msg in messages:
            if 'oaiwui_skip' in msg:
                if msg['oaiwui_skip'] == slug:
                    # keep a copy of the original message
                    stored_messages.append(copy.deepcopy(msg))
                    # delete the 'oaiwui_skip' to pass to the API
                    del msg['oaiwui_skip']
                    clean_messages.append(msg)
                else:
                    # remove the message
                    continue
            else:
                # keep the message
                stored_messages.append(msg)
                clean_messages.append(msg)

            msg_count += 1
#        print(f"##### clean messages: {clean_messages}")
#        print(f"##### clear_chat: {clear_chat} msg_count: {msg_count}")

        # Call the GPT API
        msg_file = f"{dest_dir}/msg.json"
        with open(msg_file, 'w') as f:
            json.dump(clean_messages, f, indent=4)

        # Use kwargs to max_tokens and temperature
        if self.beta_models[model_engine] is True:
            kwargs['max_completion_tokens'] = max_tokens
        else:
            kwargs['max_tokens'] = max_tokens
            kwargs['temperature'] = temperature
        err, response = simpler_gpt_call(self.apikey, clean_messages, model_engine, **kwargs)

        if cf.isNotBlank(err):
            return err, ""
        os.remove(msg_file)

        # Add the response to the messages
        stored_messages.append({ 'role': 'assistant', 'content': [ {'type': 'text', 'text': response} ] })

        run_file = f"{dest_dir}/run.json"
        run_json = {
            "role": role,
            "prompt": prompt,
            "response": response,
            'messages': stored_messages,
        }
        with open(run_file, 'w') as f:
            json.dump(run_json, f, indent=4)
        with open(self.last_runfile, 'w') as f:
            json.dump({'last_runfile': run_file}, f, indent=4)

        return "", run_file


#####
    def estimate_tokens(self, txt):
        # https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them
        word_count = len(txt.split())
        char_count = len(txt)
        return max(int(word_count / 0.75), int(char_count / 4.00))


#####
    def get_history(self):
        return cf.get_history(self.save_location)

