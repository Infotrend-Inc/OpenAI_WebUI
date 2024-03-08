import openai
from openai import OpenAI

import streamlit as st
import extra_streamlit_components as stx
from streamlit_extras.stoggle import stoggle

import json

import os.path

import common_functions as cf


#####
def gpt_call(apikey, messages, model_engine, max_tokens, temperature, **kwargs):
    client = OpenAI(api_key=apikey)

    # Generate a response (20231108: Fixed for new API version)
    try:
        completion = client.chat.completions.create(
            model=model_engine,
            messages = messages,
            max_tokens=max_tokens,
            n=1,
            stop=None,
            temperature=temperature,
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

    return "", completion.choices[0].message.content

##########
class OAI_GPT:
    def __init__(self, apikey, save_location, models_list, av_models_list):
        self.last_gpt_query = 'last_gpt_query'

        self.apikey = apikey
        self.save_location = save_location

        self.models = {}
        self.models_status = {}
        self.model_help = ""
        self.per_model_help = {}
        self.gpt_presets = {}
        self.gpt_presets_help = ""
        self.gpt_roles = {}
        self.gpt_roles_help = ""

        self.set_parameters(models_list, av_models_list)


#####
# https://platform.openai.com/docs/models/continuous-model-upgrades
    def set_parameters(self, models_list, av_models_list):
        models = {}
        models_status = {}
        model_help = ""

        s_models_list = models_list.replace(",", " ").split()
        known_models = list(av_models_list.keys())
        for t_model in s_models_list:
            model = t_model.strip()
            if model in av_models_list:
                if av_models_list[model]["status"] == "retired":
                    st.warning(f"Model {model} is retired (" + av_models_list[model]["status_details"] + "), discarding it")
                else:
                    models[model] = dict(av_models_list[model])
                    if cf.isNotBlank(models[model]["status_details"]):
                        models_status[model] = models[model]["status"] +" (" + models[model]["status_details"] + ")"
            else:
                st.error(f"Unknown model: {model} | Known models: {known_models}")
                cf.error_exit(f"Unknown model {model}")

        model_help = ""
        for key in models:
            per_model_help = f"{key} (" + models[key]["status"] + "):\n"
            per_model_help += models[key]["label"] + "\n"
            per_model_help += "[Data: " + models[key]["data"] + " | "
            per_model_help += "Tokens -- max: " + str(models[key]["max_token"]) + " / "
            per_model_help += "context: " + str(models[key]["context_token"]) + "]"
            if cf.isNotBlank(models[key]["status_details"]):
                per_model_help += " NOTE: " + models[key]["status_details"]
            self.per_model_help[key] = per_model_help
            model_help += f"{per_model_help}\n\n"
        model_help += "For list of available supported models, see https://github.com/Infotrend-Inc/OpenAI_WebUI\n\n"

        active_models = [x for x in av_models_list if av_models_list[x]["status"] == "active"]
        active_models_txt = ",".join(active_models)

        if len(models) == 0:
            st.error(f"No models retained, unable to continue. Active models: {active_models_txt}")
            cf.error_exit(f"No models retained, unable to continue.\nActive models: {active_models_txt}")

        model_help += f"List of active models: {active_models_txt}\n\n"

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


#####
    def get_rf_role_prompt_response(self, run_file):
        run_json = cf.get_run_file(run_file)
        role = ""
        if 'role' in run_json:
            role = run_json['role']
        prompt = ""
        if 'prompt' in run_json:
            prompt = run_json['prompt']
        response = ""
        if 'response' in run_json:
            response = run_json['response']
        return (role, prompt, response)


#####
    def get_dest_dir(self):
        return os.path.join(self.save_location, "gpt", cf.get_timeUTC())


#####
    def format_rpr(self, role, prompt, response):
        return (f"\n\n--------------------------\n\n -- role: {role}\n\n -- prompt: {prompt}\n\n -- response: {response }\n\n")

#####
    def get_chat_history(self, run_file):
        run_json = cf.get_run_file(run_file)
        if 'last_run_file' in run_json:
            (role, prompt, response) = self.get_rf_role_prompt_response(run_file)
            txt = self.format_rpr(role, prompt, response)
            last_run_file = run_json['last_run_file']
            if cf.isNotBlank(last_run_file):
                err = cf.check_file_r(last_run_file)
                if cf.isNotBlank(err):
                    return(f"A previous run file does not exist {last_run_file}, it might have been deleted, truncating chat history\n\n" + txt)
                tmp = self.get_chat_history(last_run_file)
                return (self.get_chat_history(last_run_file) + txt)
            else:
                return (txt)
        else: # last one, return the formatted text
            (role, prompt, response) = self.get_rf_role_prompt_response(run_file)
            return(self.format_rpr(role, prompt, response))


#####
    def chatgpt_it(self, model_engine, prompt, max_tokens, temperature, dest_dir, clear_chat, role, **kwargs):
        err = cf.check_existing_dir_w(dest_dir)
        if cf.isNotBlank(err):
            st.error(f"While checking {dest_dir}: {err}")
            cf.error_exit(err)

        messages = []
        last_run_file = None
        if not clear_chat:
            # Obtain previous messages
            if self.last_gpt_query in st.session_state:
                run_file = st.session_state[self.last_gpt_query]
                old_run_json = cf.get_run_file(run_file)
                if 'messages' in old_run_json:
                    messages = old_run_json['messages']
                    last_run_file = run_file

        messages.append({ 'role': role, 'content': prompt })

        err, response = gpt_call(self.apikey, messages, model_engine, max_tokens, temperature, **kwargs)
        if cf.isNotBlank(err):
            return err, ""

        runid = cf.get_runid()
        run_file = f"{dest_dir}/run---{runid}.json"
        run_json = {
            "role": role,
            "prompt": prompt,
            "response": response,
            'messages': messages,
            'last_run_file': last_run_file,
        }
        with open(run_file, 'w') as f:
            json.dump(run_json, f, indent=4)

        return "", run_file


#####
    def estimate_tokens(self, txt):
        # https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them
        word_count = len(txt.split())
        char_count = len(txt)
        return max(int(word_count / 0.75), int(char_count / 4.00))


#####
    def get_history(self):
        search_dir = os.path.join(self.save_location, "gpt")
        return cf.get_history(search_dir)

#####
    def set_ui(self):
        st.sidebar.empty()
        with st.sidebar:
            st.text("Check the various ? for help", help=f"[Run Details]\n\nRunID: {cf.get_runid()}\n\nSave location: {self.save_location}\n\nUTC time: {cf.get_timeUTC()}\n")
            model = st.selectbox("model", options=list(self.models.keys()), index=0, key="model", help=self.model_help)
            if model in self.models_status:
                st.info(f"{model}: {self.models_status[model]}")
            m_token = self.models[model]['max_token']
            role = st.selectbox("Role", options=self.gpt_roles, index=0, key="input_role", help = "Role of the input text\n\n" + self.gpt_roles_help)
            clear_chat = st.toggle(label="Clear next query's chat history", value=False, help="This will clear the chat history for the next query. This is useful when you want to start a new chat with a fresh context.")
            max_tokens = st.slider('max_tokens', 0, m_token, 1000, 100, "%i", "max_tokens", "The maximum number of tokens to generate in the completion. The token count of your prompt plus max_tokens cannot exceed the model\'s context length.")
            temperature = st.slider('temperature', 0.0, 1.0, 0.5, 0.01, "%0.2f", "temperature", "The temperature of the model. Higher temperature results in more surprising text.")
            presets = st.selectbox("Preset", options=list(self.gpt_presets.keys()), index=0, key="presets", help=self.gpt_presets_help)
            gpt_show_tooltip = st.toggle(label="Show Tips", value=True, help="Show some tips on how to use the tool", key="gpt_show_tooltip")
            gpt_show_history = st.toggle(label='Show Prompt History', value=False, help="Show a list of prompts that you have used in the past (most recent first). Loading a selected prompt does not load the parameters used for the generation.", key="gpt_show_history")
            if gpt_show_history:
                gpt_allow_history_deletion = st.toggle('Allow Prompt History Deletion', value=False, help="This will allow you to delete a prompt from the history. This will delete the prompt and all its associated files. This cannot be undone.", key="gpt_allow_history_deletion")


        if gpt_show_tooltip:
            stoggle('Tips', 'GPT provides a simple but powerful interface to any models. You input some text as a prompt, and the model will generate a text completion that attempts to match whatever context or pattern you gave it:<br>- The tool works on text to: answer questions, provide definitions, translate, summarize, and analyze sentiments.<br>- Keep your prompts clear and specific. The tool works best when it has a clear understanding of what you\'re asking it, so try to avoid vague or open-ended prompts.<br>- Use complete sentences and provide context or background information as needed.<br>- Some presets are available in the sidebar, check their details for more information.<br>A few example prompts (to use with "None" preset):<br>- Create a list of 8 questions for a data science interview<br>- Generate an outline for a blog post on MFT<br>- Translate "bonjour comment allez vous" in 1. English 2. German 3. Japanese<br>- write python code to display with an image selector from a local directory using OpenCV<br>- Write a creative ad and find a name  for a container to run machine learning and computer vision algorithms by providing access to many common ML frameworks<br>- some models support "Chat" conversations. If you see the "Clear Chat" button, this will be one such model. They also support different max tokens, so adapt accordingly. The "Clear Chat" is here to allow you to start a new "Chat". Chat models can be given writing styles using the "system" "role"<br>More examples and hints can be found at https://platform.openai.com/examples')

        if gpt_show_history:
            hist = self.get_history()
            if len(hist) == 0:
                st.warning("No prompt history found")
            else:
                cf.show_history(hist, gpt_allow_history_deletion, 'gpt_last_prompt', self.last_gpt_query)

        if 'gpt_last_prompt' not in st.session_state:
            st.session_state['gpt_last_prompt'] = ''
        prompt_value=f"GPT ({model}) Input (role: {role}) [max_tokens: {max_tokens} | temperature: {temperature} | preset: {presets}]"
        help_text = self.per_model_help[model] if model in self.per_model_help else "No help available for this model"
        prompt = st.empty().text_area(prompt_value, st.session_state['gpt_last_prompt'], placeholder="Enter your prompt", key="input", help=help_text)
        st.session_state['gpt_last_prompt'] = prompt

        if st.button("Request Answer", key="request_answer"):
            if cf.isBlank(prompt) or len(prompt) < 10:
                st.error("Please provide a prompt of at least 10 characters before requesting an answer", icon="✋")
                return ()

            prompt = self.gpt_presets[presets]["pre"] + prompt + self.gpt_presets[presets]["post"]
            prompt_token_count = self.estimate_tokens(prompt)
            requested_token_count = prompt_token_count + max_tokens
            if requested_token_count > self.models[model]["context_token"]:
                st.warning("You requested an estimated %i tokens, which might exceed the model's context window of %i tokens. We are still proceeding with the request, but an error return is possible." % (requested_token_count, self.models[model]["context_token"]))

            if max_tokens > 0:
                gpt_dest_dir = self.get_dest_dir()
                cf.make_wdir_error(gpt_dest_dir)
                with st.spinner(f"Asking OpenAI ({model} for {max_tokens} tokens with temperature {temperature}. Prompt est. tokens : {prompt_token_count})"):
                    err, run_file = self.chatgpt_it(model, prompt, max_tokens, temperature, gpt_dest_dir, clear_chat, role, **self.gpt_presets[presets]["kwargs"])
                    if cf.isNotBlank(err):
                        st.error(err)
                    if cf.isNotBlank(run_file):
                        st.session_state[self.last_gpt_query] = run_file
                        st.toast("Done")

        if self.last_gpt_query in st.session_state:
            run_file = st.session_state[self.last_gpt_query]
            run_json = cf.get_run_file(run_file)

            prompt = run_json["prompt"]
            response = run_json["response"]
            messages = []
            if 'messages' in run_json:
                messages = run_json["messages"]

            stoggle('Original Prompt', prompt)
            chat_history = ""
            if len(messages) > 0:
                chat_history = self.get_chat_history(run_file)
                stoggle('Chat History', chat_history)

            option_list = ('Text (no wordwrap)', 'Text (wordwrap, may cause some visual inconsistencies)',
                        'Code (automatic highlighting for supported languages)')
            option = st.selectbox('Display mode:', option_list)

            if option == option_list[0]:
                st.text(response)
            elif option == option_list[1]:
                st.markdown(response)
            elif option == option_list[2]:
                st.code(response)
            else:
                st.error("Unknown display mode")

            query_output = prompt + "\n\n--------------------------\n\n" + response
            if len(messages) > 1:
                col1, col2, col3 = st.columns(3)
                col1.download_button(label="Download Latest Result", data=response)
                col2.download_button(label="Download Latest Query+Result", data=query_output)
                col3.download_button(label="Download Chat Query+Result", data=chat_history)
            else:
                col1, col2 = st.columns(2)
                col1.download_button(label="Download Result", data=response)
                col2.download_button(label="Download Query+Result", data=query_output)
