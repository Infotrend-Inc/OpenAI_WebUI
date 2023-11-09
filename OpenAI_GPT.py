import openai
from openai import OpenAI

import streamlit as st
import extra_streamlit_components as stx
from streamlit_toggle import st_toggle_switch
from streamlit_extras.stoggle import stoggle

import json

import os.path

import common_functions as cf


#####
def gpt_call(apikey, messages, model_engine, max_tokens, temperature, **kwargs):
    client = OpenAI(api_key=apikey)

    # Generate a response (20231108: Fixed for new API version)
    # https://platform.openai.com/docs/guides/error-codes/python-library-error-types
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
    except openai.APIError as e:
        return(f"OpenAI API returned an API Error: {e}", "")
    except openai.Timeout as e:
        return(f"OpenAI API request timed out: {e}", "")
    except openai.APIConnectionError as e:
        return(f"OpenAI API request failed to connect: {e}", "")
    except openai.InvalidRequestError as e:
        return(f"OpenAI API request was invalid: {e}", "")
    except openai.AuthenticationError as e:
        return(f"OpenAI API request was not authorized: {e}", "")
    except openai.PermissionError as e:
        return(f"OpenAI API request was not permitted: {e}", "")
    except openai.RateLimitError as e:
        return(f"OpenAI API request exceeded rate limit: {e}", "")
    except openai.OpenAIError as e:
        return(f"OpenAI API request failed: {e}", "")

    return "", completion.choices[0].message.content

##########
class OAI_GPT:
    def __init__(self, apikey, save_location, models_list):
        self.last_gpt_query = 'last_gpt_query'

        self.apikey = apikey
        self.save_location = save_location

        self.models_supported = models_list
        self.set_parameters(models_list)


#####
# https://platform.openai.com/docs/models/continuous-model-upgrades
    def set_parameters(self, models_list):
        models = {}
        model_help = ""

        all = {
            "gpt-3.5-turbo":
            {
                "label": "Most capable GPT-3.5 model and optimized for chat. Will be updated with OpenAI's latest model iteration. For many basic tasks, the difference between GPT-4 and GPT-3.5 models is not significant. However, in more complex reasoning situations, GPT-4 is much more capable.",
                "max_token": 4000,
                "data": "Up to Sep 2021 (as of 20231108)"
            },
            "gpt-3.5-turbo-16k":
            {
                "label": "Same capabilities as the standard gpt-3.5-turbo model but with 4 times the context.",
                "max_token": 16000,
                "data": "Up to Sep 2021 (as of 20231108)"
            },
            "gpt-4":
            {
                "label": "More capable than any GPT-3.5 model, able to do more complex tasks, and optimized for chat.",
                "max_token": 8192,
                "data": "Up to Sep 2021 (as of 20231108)"
            },
            "gpt-4-32k":
            {
                "label": "Same capabilities as the base gpt-4 mode but with 4x the context length.",
                "max_token": 32768,
                "data": "Up to Sep 2021 (as of 20231108)"
            },
            "gpt-4-1106-preview":
            {
                "label": "The latest GPT-4 model (with 128k tokens) with improved instruction following, JSON mode, reproducible outputs, parallel function calling, and more. Returns a maximum of 4,096 output tokens. This preview model is not yet suited for production traffic.",
                "max_token": 4096,
                "data": "Up to Apr 2023 (as of 20231108)"
            }
        }

        s_models_list = models_list.split(",")  
        for model in s_models_list:
            if model in all:
                models[model] = all[model]
            else:
                cf.error_exit(f"Unknown model {model}")

        model_help = ""
        for key in models:
            model_help += key + ":\n"
            model_help += models[key]["label"] + "\n"
            model_help += "max_token: " + str(models[key]["max_token"]) + "\n"
            model_help += "data: " + models[key]["data"] + "\n\n"

        self.models = models
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
    def set_ui(self):
        st.sidebar.empty()
        with st.sidebar:
            st.text("Please check the ? for help")
            model = st.selectbox("model", options=list(self.models.keys()), index=0, key="model", help=self.model_help)
            m_token = self.models[model]['max_token']
            role = st.selectbox("Role", options=self.gpt_roles, index=0, key="input_role", help = "Role of the input text\n\n" + self.gpt_roles_help)
            clear_chat = st_toggle_switch(label="Clear chat history for next query", default_value=False, label_after=False, key="clear_chat")
            max_tokens = st.slider('max_tokens', 0, m_token, 1000, 100, "%i", "max_tokens", "The maximum number of tokens to generate in the completion. The token count of your prompt plus max_tokens cannot exceed the model\'s context length.")
            temperature = st.slider('temperature', 0.0, 1.0, 0.5, 0.01, "%0.2f", "temperature", "The temperature of the model. Higher temperature results in more surprising text.")
            presets = st.selectbox("Preset", options=list(self.gpt_presets.keys()), index=0, key="presets", help=self.gpt_presets_help)
            show_tooltip = st_toggle_switch(label="Show Tips", key="show_tips", default_value=True, label_after=False)

        if show_tooltip:
            stoggle('Tips', 'GPT provides a simple but powerful interface to any models. You input some text as a prompt, and the model will generate a text completion that attempts to match whatever context or pattern you gave it:<br>- The tool works on text to: answer questions, provide definitions, translate, summarize, and analyze sentiments.<br>- Keep your prompts clear and specific. The tool works best when it has a clear understanding of what you\'re asking it, so try to avoid vague or open-ended prompts.<br>- Use complete sentences and provide context or background information as needed.<br>- Some presets are available in the sidebar, check their details for more information.<br>A few example prompts (to use with "None" preset):<br>- Create a list of 8 questions for a data science interview<br>- Generate an outline for a blog post on MFT<br>- Translate "bonjour comment allez vous" in 1. English 2. German 3. Japanese<br>- write python code to display with an image selector from a local directory using OpenCV<br>- Write a creative ad and find a name  for a container to run machine learning and computer vision algorithms by providing access to many common ML frameworks<br>- some models support "Chat" conversations. If you see the "Clear Chat" button, this will be one such model. They also support different max tokens, so adapt accordingly. The "Clear Chat" is here to allow you to start a new "Chat". Chat models can be given writing styles using the "system" "role"<br>More examples and hints can be found at https://platform.openai.com/examples')

        prompt_value=f"GPT ({model}) Input"
        prompt_value += f" (role: {role})"
        prompt_value += f" [max_tokens: {max_tokens} | temperature: {temperature} | preset: {presets}]"
        prompt = st.empty().text_area(prompt_value, "", placeholder="Enter your prompt", key="input")

        if st.button("Request Answer", key="request_answer"):
            if cf.isBlank(prompt) or len(prompt) < 10:
                st.error("Please provide a prompt of at least 10 characters before requesting an answer", icon="✋")
                return ()

            prompt = self.gpt_presets[presets]["pre"] + prompt + self.gpt_presets[presets]["post"]
            prompt_token_count = self.estimate_tokens(prompt)
            requested_token_count = prompt_token_count + max_tokens
            used_max_tokens = 0
            if requested_token_count > self.models[model]["max_token"]:
                used_max_tokens = self.models[model]["max_token"] - prompt_token_count
                if used_max_tokens < 0:
                    st.error("You have exceeded the maximum number of tokens allowed by the model", icon="✋")
                else:
                    st.warning("You requested %i tokens, but the model can only generate %i tokens. Requesting at max %i tokens." % (requested_token_count, self.models[model]["max_token"], used_max_tokens), icon="❌")
            else:
                used_max_tokens = max_tokens

            if used_max_tokens > 0:
                gpt_dest_dir = self.get_dest_dir()
                cf.make_wdir_error(gpt_dest_dir)
                with st.spinner(f"Asking OpenAI ({model} for {used_max_tokens} tokens with temperature {temperature}. Prompt est. tokens : {prompt_token_count})"):
                    err, run_file = self.chatgpt_it(model, prompt, used_max_tokens, temperature, gpt_dest_dir, clear_chat, role, **self.gpt_presets[presets]["kwargs"])
                    if cf.isNotBlank(err):
                        st.error(err)
                    if cf.isNotBlank(run_file):
                        st.session_state['last_gpt_query'] = run_file
                        st.info("Done")


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
