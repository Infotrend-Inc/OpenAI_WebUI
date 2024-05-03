import openai
from openai import OpenAI

import streamlit as st
import extra_streamlit_components as stx
from streamlit_extras.stoggle import stoggle

import json

import os.path

import common_functions as cf
import common_functions_WUI as cfw

import OpenAI_GPT as OAI_GPT

##########
class OAI_GPT_WUI:
    def __init__(self, oai_gpt: OAI_GPT) -> None:
        self.last_gpt_query = "last_gpt_query"

        self.oai_gpt = oai_gpt
        self.save_location = oai_gpt.get_save_location()
        self.models = oai_gpt.get_models()
        self.model_help = oai_gpt.get_model_help()
        self.models_status = oai_gpt.get_models_status()
        self.gpt_roles = oai_gpt.get_gpt_roles()
        self.gpt_roles_help = oai_gpt.get_gpt_roles_help()
        self.gpt_presets = oai_gpt.get_gpt_presets()
        self.gpt_presets_help = oai_gpt.get_gpt_presets_help()
        self.per_model_help = oai_gpt.get_per_model_help()


#####
    def set_ui(self):
        st.sidebar.empty()
        with st.sidebar:
            st.text("Check the various ? for help", help=f"[Run Details]\n\nRunID: {cfw.get_runid()}\n\nSave location: {self.save_location}\n\nUTC time: {cf.get_timeUTC()}\n")
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
            err, hist = self.oai_gpt.get_history()
            if cf.isNotBlank(err):
                st.error(err)
                cf.error_exit(err)
            if len(hist) == 0:
                st.warning("No prompt history found")
            else:
                cfw.show_history(hist, gpt_allow_history_deletion, 'gpt_last_prompt', self.last_gpt_query)

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
            prompt_token_count = self.oai_gpt.estimate_tokens(prompt)
            requested_token_count = prompt_token_count + max_tokens
            if requested_token_count > self.models[model]["context_token"]:
                st.warning("You requested an estimated %i tokens, which might exceed the model's context window of %i tokens. We are still proceeding with the request, but an error return is possible." % (requested_token_count, self.models[model]["context_token"]))

            if max_tokens > 0:
                with st.spinner(f"Asking OpenAI ({model} for {max_tokens} tokens with temperature {temperature}. Prompt est. tokens : {prompt_token_count})"):
                    err, run_file = self.oai_gpt.chatgpt_it(model, prompt, max_tokens, temperature, clear_chat, role, **self.gpt_presets[presets]["kwargs"])
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
                chat_history = self.oai_gpt.get_chat_history(run_file)
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
