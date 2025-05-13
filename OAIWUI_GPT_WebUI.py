import openai
from openai import OpenAI

import streamlit as st
import extra_streamlit_components as stx
from streamlit_extras.stoggle import stoggle

from PIL import Image
import base64
import io
import math

import json
import copy

import os.path
import tempfile

import common_functions as cf
import common_functions_WebUI as cfw

import OAIWUI_GPT as OAIWUI_GPT

##########
class OAIWUI_GPT_WebUI:
    def __init__(self, oaiwui_gpt: OAIWUI_GPT, enable_vision: bool = True, prompt_presets_dir: str = None, prompt_presets_file: str = None) -> None:
        self.last_gpt_query = "last_gpt_query"

        self.oaiwui_gpt = oaiwui_gpt
        self.save_location = oaiwui_gpt.get_save_location()
        self.models = oaiwui_gpt.get_models()
        self.model_help = oaiwui_gpt.get_model_help()
        self.models_status = oaiwui_gpt.get_models_status()
        self.model_capability = oaiwui_gpt.get_model_capability()
        self.gpt_roles = oaiwui_gpt.get_gpt_roles()
        self.gpt_roles_help = oaiwui_gpt.get_gpt_roles_help()
        self.gpt_presets = oaiwui_gpt.get_gpt_presets()
        self.gpt_presets_help = oaiwui_gpt.get_gpt_presets_help()

        self.per_model_help = oaiwui_gpt.get_per_model_help()
        self.beta_models = oaiwui_gpt.get_beta_models()
        self.per_model_provider = oaiwui_gpt.get_per_model_provider()
        self.per_model_meta = oaiwui_gpt.get_per_model_meta()

        self.enable_vision = enable_vision

        self.prompt_presets_dir = prompt_presets_dir
        self.prompt_presets = {}

        self.prompt_presets_file = prompt_presets_file
        self.prompt_presets_settings = {}

        self.models_warning = oaiwui_gpt.get_models_warning()
        self.known_models = oaiwui_gpt.get_known_models()

        err = self.load_prompt_presets()
        if cf.isNotBlank(err):
            st.error(err)
            cf.error_exit(err)


    def resize_rectangle(self, original_width, original_height, max_width, max_height):
        aspect_ratio = original_width / original_height
        max_area = max_width * max_height
        original_area = original_width * original_height

        # Calculate scaling factor for proportional fit
        scale_factor = math.sqrt(max_area / original_area)

        # Scale the dimensions
        new_width = original_width * scale_factor
        new_height = original_height * scale_factor

        # Check if resizing would make the rectangle larger
        if new_width >= original_width or new_height >= original_height:
            return original_width, original_height
    
        # Adjust if necessary to fit within max dimensions
        if new_width > max_width:
            new_width = max_width
            new_height = new_width / aspect_ratio

        if new_height > max_height:
            new_height = max_height
            new_width = new_height * aspect_ratio

        return new_width, new_height

    def img_resize_core(self, im, max_x, max_y):
        new_x, new_y = self.resize_rectangle(im.size[0], im.size[1], max_x, max_y)
        return int(new_x), int(new_y)

    def img_resize(self, tfilen, details_selection):
        with Image.open(tfilen) as im:
            new_x, new_y = im_x, im_y = im.size[0], im.size[1]
            if details_selection == "low":
                new_x, new_y = self.img_resize_core(im, 512, 512)
            else:
                new_x, new_y = self.img_resize_core(im, 2048, 2048)

            if new_x == im_x and new_y == im_y:
                return new_x, new_y

            im = im.resize((new_x, new_y))
            im.save(tfilen, format="png")
            return new_x, new_y


    def image_uploader(self, details_selection):
        # image uploader: PNG (.png), JPEG (.jpeg and .jpg), WEBP (.webp), and non-animated GIF (.gif).
        uploaded_file = st.file_uploader("Upload a PNG/JPEG/WebP image (automatic resize to a value closer to the selected \"details\" selected, see its \"?\")", type=['png','jpg','jpeg','webp'])
        if uploaded_file is not None:
            placeholder = st.empty()
            tfile = tempfile.NamedTemporaryFile(delete=False)
            tfilen = str(tfile.name)
            with open(tfilen, "wb") as outfile:
                outfile.write(uploaded_file.getvalue())

            # confirm it is a valid PNG, JPEG, WEBP image
            im_fmt = None
            im_det = None
            im_area = None
            try:
                with Image.open(tfilen) as im:
                    im_fmt = im.format
                    im_det = f"{im.size[0]}x{im.size[1]}"
            except OSError:
                pass

            if im_fmt == "PNG" or im_fmt == "JPEG" or im_fmt == "WEBP":
                im_x, im_y = self.img_resize(tfilen, details_selection)
                tk_cst = (170 * im_x * im_y) // (512*512) + 85
                tk_cst = 1105 if tk_cst > 1105 else tk_cst # following the details of "Calculating costs"
                n_img_det = f"{im_x}x{im_y}"
                res_txt = f"resized to: {n_img_det} " if n_img_det != im_det else ""
                tkn_txt = f"(est. token cost -- \"high\": {tk_cst} | \"low\": 85)"
                placeholder.info(f"Uploaded image: {im_fmt} orig size: {im_det} {res_txt} {tkn_txt}")
                return tfilen
            else:
                placeholder.error(f"Uploaded image ({im_fmt}) is not a valid/supported PNG, JPEG, or WEBP image")
                return None

        return None

#####

    def load_prompt_presets(self):
        if self.prompt_presets_dir is None:
            return ""

        prompt_presets = {}
        for file in os.listdir(self.prompt_presets_dir):
            if file.endswith(".json"):
                err = cf.check_file_r(os.path.join(self.prompt_presets_dir, file))
                if cf.isNotBlank(err):
                    return err
                with open(os.path.join(self.prompt_presets_dir, file), "r") as f:
                    prompt_presets[file.split(".json")[0]] = json.load(f)

        self.prompt_presets = prompt_presets

        if self.prompt_presets_file is not None:
            err = cf.check_file_r(self.prompt_presets_file)
            if cf.isNotBlank(err):
                return err
            with open(self.prompt_presets_file, "r") as f:
                self.prompt_presets_settings = json.load(f)
            if 'model' not in self.prompt_presets_settings:
                return f"Could not find 'model' in {self.prompt_presets_file}"
            model = self.prompt_presets_settings['model']
            if model not in self.models:
                return f"Could not find requested 'model' ({model}) in available models: {list(self.models.keys())} (from {self.prompt_presets_file})"
            if 'tokens' not in self.prompt_presets_settings:
                return f"Could not find 'tokens' in {self.prompt_presets_file}"
            tmp = self.prompt_presets_settings['tokens']
            if tmp is None:
                return f"Invalid 'tokens' ({tmp}) in {self.prompt_presets_file}"
            if tmp <= 0:
                return f"Invalid 'tokens' ({tmp}) in {self.prompt_presets_file}"
            if tmp > self.models[model]['max_token']:
                return f"Requested 'tokens' ({tmp}) is greater than model's 'max_token' ({self.models[model]['max_token']}) in {self.prompt_presets_file}"
            if 'temperature' not in self.prompt_presets_settings:
                return f"Could not find 'temperature' in {self.prompt_presets_file}"
            tmp = self.prompt_presets_settings['temperature']
            if tmp is None:
                return f"Invalid 'temperature' ({tmp}) in {self.prompt_presets_file}"
            if tmp < 0:
                return f"Invalid 'temperature' ({tmp}) in {self.prompt_presets_file}"
            if tmp > 1:
                return f"Invalid 'temperature' ({tmp}) in {self.prompt_presets_file}"

        return ""


#####
    def set_ui(self):
        st.sidebar.empty()
        vision_capable = False
        websearch_capable = False
        vision_mode = False
        disable_preset_prompts = False
        prompt_preset = None
        msg_extra = None
        beta_model = False

        temperature_selector = True
        tokens_selector = True
        max_tokens_selector = True
        role_selector = True
        preset_selector = False
        prompt_preset_selector = True

        # models used since last clear chat
        if 'model_used' not in st.session_state:
            st.session_state.model_used = []

        base_model_list = list(self.models.keys())
        model_list = []
        for model_name in base_model_list:
            model_provider = self.per_model_provider[model_name] if model_name in self.per_model_provider else "Unknown"
            model_list.append(f"{model_name} ({model_provider})")

        if 'gpt_messages' not in st.session_state:
            st.session_state.gpt_messages = []
        else:
            disable_preset_prompts = False

        with st.sidebar:
            st.text("Check the various ? for help", help=f"[Run Details]\n\nRunID: {cfw.get_runid()}\n\nSave location: {self.save_location}\n\nUTC time: {cf.get_timeUTC()}\n")

            if st.button("Clear Chat"):
                st.session_state.gpt_messages = []
                disable_preset_prompts = False
                if self.last_gpt_query in st.session_state:
                    del st.session_state[self.last_gpt_query]
                if 'gpt_msg_extra' in st.session_state:
                    del st.session_state['gpt_msg_extra'] # only a clear will allow us to set msg_extra again
                st.session_state.model_used = []

            # create a location placeholder for the prompt preset selector
            st_preset_placeholder = st.empty()

            if self.prompt_presets_settings == {}:
                # Only available if not in "preset only" mode
                tmp_model_name = st.selectbox("model", options=model_list, index=0, key="model_name", help=self.model_help)
                model_name = tmp_model_name.split(" ")[0]
                if model_name in self.models_status:
                    st.info(f"{model_name}: {self.models_status[model_name]}")
                if "vision" in self.model_capability[model_name]:
                    vision_capable = True
                if "websearch" in self.model_capability[model_name]:
                    websearch_capable = True

                roles_toremove = []
                if model_name in self.per_model_meta and "removed_roles" in self.per_model_meta[model_name]:
                    roles_toremove = self.per_model_meta[model_name]["removed_roles"]

                if model_name in self.per_model_meta and "disabled_features" in self.per_model_meta[model_name]:
                    disabled_features = self.per_model_meta[model_name]["disabled_features"]
                    if "prompt_preset" in disabled_features:
                        prompt_preset_selector = False
                    if "preset" in disabled_features:
                        preset_selector = False
                    if "role" in disabled_features:
                        role_selector = False
                    if "temperature" in disabled_features:
                        temperature_selector = False
                    if "max_tokens" in disabled_features:
                        max_tokens_selector = False
                    if "tokens" in disabled_features:
                        tokens_selector = False
                        
                if model_name in self.beta_models and self.beta_models[model_name] is True:
                    beta_model = True

                m_token = self.models[model_name]['max_token']

                # vision mode bypass
                if self.enable_vision is False:
                    vision_mode = False
                    vision_capable = False

                if vision_capable:
                    vision_mode = st.toggle(label="Vision", value=False, help="Enable the upload of an image. Vision's limitation and cost can be found at https://platform.openai.com/docs/guides/vision/limitations.\n\nDisables the role and presets selectors. Image(s) are resized when over the max of the \'details\' selected. Please be aware that each 512px x 512px title is expected to cost 170 tokens. Using this mode disables roles, presets and chat (the next prompt will not have knowledge of past thread of conversation)")

                if vision_mode:
                    vision_details = st.selectbox("Vision Details", options=["auto", "low", "high"], index=0, key="vision_details", help="The model will use the auto setting which will look at the image input size and decide if it should use the low or high setting.\n\n- low: the model will receive a low-res 512px x 512px version of the image, and represent the image with a budget of 85 tokens. This allows the API to return faster responses and consume fewer input tokens for use cases that do not require high detail.\n\n- high will first allows the model to first see the low res image (using 85 tokens) and then creates detailed crops using 170 tokens for each 512px x 512px tile.\n\n\n\nImage inputs are metered and charged in tokens, just as text inputs are. The token cost of a given image is determined by two factors: its size, and the detail option on each image_url block. All images with detail: low cost 85 tokens each. detail: high images are first scaled to fit within a 2048 x 2048 square, maintaining their aspect ratio. Then, they are scaled such that the shortest side of the image is 768px long. Finally, a count of how many 512px squares the image consists of is performed. Each of those squares costs 170 tokens. Another 85 tokens are always added to the final total. More details at https://platform.openai.com/docs/guides/vision/calculating-costs")
                    role_selector = False
                    preset_selector = False

                img_file = None
                if vision_mode:
                    img_file = self.image_uploader(vision_details)
                    img_type = "png" # convert everything to PNG for processing
                    if img_file is not None:
                        img_b64 = None
                        img_bytes = io.BytesIO()
                        with Image.open(img_file) as image:
                            image.save(img_bytes, format=img_type)
                            img_b64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
                        if img_b64 is not None:
                            img_str = f"data:image/{img_type};base64,{img_b64}"
                            msg_extra = [ 
                                { 
                                    "role": "user", 
                                    "content": [
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": img_str,
                                                "details": vision_details
                                            }
                                        }
                                    ],
                                    "oaiwui_skip": True,
                                    "oaiwui_vision": True
                                }
                            ]
                        if os.path.exists(img_file):
                            os.remove(img_file)

                role = list(self.gpt_roles.keys())[0]
                if role_selector is True:
                    tmp_roles = self.gpt_roles.copy()
                    for r in roles_toremove:
                        tmp_roles.pop(r)
                    tmp_txt = "" if beta_model is False else "\n\nBeta models do not support the 'system' role"
                    role = st.selectbox("Role", options=tmp_roles, index=0, key="input_role", help = "Role of the input text\n\n" + self.gpt_roles_help + tmp_txt)

                max_tokens = 1000
                if max_tokens_selector is True:
                    if beta_model is False:
                        max_tokens = st.slider('max_tokens', 0, m_token, 1000, 100, "%i", "max_tokens", "The maximum number of tokens to generate in the completion. The token count of your prompt plus max_tokens cannot exceed the model\'s context length.")
                    else:
                        max_tokens = st.slider('max_completion_tokens', 0, m_token, 4000, 100, "%i", "max_completion_tokens", "For beta models: control the total number of tokens generated by the model, including both reasoning and visible completion tokens. If the token value is too low, the answer might be empty")

                temperature = 0.5
                if temperature_selector is True:
                    temperature = st.slider('temperature', 0.0, 1.0, 0.5, 0.01, "%0.2f", "temperature", "The temperature of the model. Higher temperature results in more surprising text.")

                websearch = "low"
                if websearch_capable is True:
                    websearch = st.selectbox('Search Context Size', options=["low", "medium", "high"], index=0, help="Controls how much context is retrieved from the web to help the tool formulate a response.", key="websearch")

                if preset_selector is True:
                    presets = st.selectbox("GPT Task", options=list(self.gpt_presets.keys()), index=0, key="presets", help=self.gpt_presets_help)
                else:
                    presets = list(self.gpt_presets.keys())[0]
            
            else: # "preset only" mode
                model_name = self.prompt_presets_settings['model']
                max_tokens = self.prompt_presets_settings['tokens']
                temperature = self.prompt_presets_settings['temperature']
                presets = list(self.gpt_presets.keys())[0]
                role = list(self.gpt_roles.keys())[0]

            model_provider = self.per_model_provider[model_name] if model_name in self.per_model_provider else "Unknown"

            # use the location of the placeholder now that we have the vision settings
            if prompt_preset_selector is True:
                if self.prompt_presets_dir is not None:
                    prompt_preset = st_preset_placeholder.selectbox("Prompt preset", options=list(self.prompt_presets.keys()), index=None, key="prompt_preset", help="Load a prompt preset. Can only be used with new chats.", disabled=disable_preset_prompts)
                    if prompt_preset is not None:
                        if prompt_preset not in self.prompt_presets:
                            st_preset_placeholder.warning(f"Unkown {prompt_preset}")
                        else:
                            if 'messages' in self.prompt_presets[prompt_preset]:
                                if 'gpt_msg_extra' not in st.session_state:
                                    msg_extra = self.prompt_presets[prompt_preset]["messages"]
                                    st.session_state['gpt_msg_extra'] = msg_extra
                                    # clear the chat history in the GPT call as well
                    else:
                        if 'gpt_msg_extra' in st.session_state:
                            del st.session_state['gpt_msg_extra']

            gpt_show_history = st.toggle(label='Show Prompt History', value=False, help="Show a list of prompts that you have used in the past (most recent first). Loading a selected prompt does not load the parameters used for the generation.", key="gpt_show_history")
            if gpt_show_history:
                gpt_allow_history_deletion = st.toggle('Allow Prompt History Deletion', value=False, help="This will allow you to delete a prompt from the history. This will delete the prompt and all its associated files. This cannot be undone.", key="gpt_allow_history_deletion")

            download_placeholder = st.empty()

            prompt_value=f"Model: {model_name} ({model_provider}) "
            prompt_value += f"[role: {role} "
            if tokens_selector is True:
                prompt_value += f"| max_tokens: {max_tokens} "
            if temperature_selector is True:
                prompt_value += f"| temperature: {temperature}"
            if vision_mode:
                prompt_value += f" | vision details: {vision_details}"
            if preset_selector is True:
                prompt_value += f" | preset: {presets}"
            if prompt_preset_selector is True:
                if prompt_preset is not None:
                    prompt_value += f" | prompt preset: {prompt_preset}"
            if websearch_capable:
                prompt_value += f" | websearch: {websearch}"
            prompt_value += f" ]"
            st.text(prompt_value, help=f'GPT provides a simple but powerful interface to any models. You input some text as a prompt, and the model will generate a text completion that attempts to match whatever context or pattern you gave it:\n\n - The tool works on text to: answer questions, provide definitions, translate, summarize, and analyze sentiments.\n\n- Keep your prompts clear and specific. The tool works best when it has a clear understanding of what you\'re asking it, so try to avoid vague or open-ended prompts.\n\n- Use complete sentences and provide context or background information as needed.\n\n- Some presets are available in the sidebar, check their details for more information.\n\nA few example prompts (to use with "None" preset):\n\n- Create a list of 8 questions for a data science interview\n\n- Generate an outline for a blog post on MFT\n\n- Translate "bonjour comment allez vous" in 1. English 2. German 3. Japanese\n\n- write python code to display with an image selector from a local directory using OpenCV\n\n- Write a creative ad and find a name  for a container to run machine learning and computer vision algorithms by providing access to many common ML frameworks\n\n- some models support "Chat" conversations. If you see the "Clear Chat" button, this will be one such model. They also support different max tokens, so adapt accordingly. The "Clear Chat" is here to allow you to start a new "Chat". Chat models can be given writing styles using the "system" "role"\n\nMore examples and hints can be found at https://platform.openai.com/examples')

            # Check for model warnings
            if list(self.models_warning.keys()) != []:
                warning_text = " - " +"\n - ".join ([f"{model}: {self.models_warning[model]}" for model in sorted(self.models_warning.keys())])
                warning_text += f"\n\n\nKnown models: {self.known_models}"
                st.text("⚠️ Models warnings", help=f"{warning_text}")

        # Main window

        if gpt_show_history:
            err, hist = self.oaiwui_gpt.get_history()
            if cf.isNotBlank(err):
                st.error(err)
                cf.error_exit(err)
            if len(hist) == 0:
                st.warning("No prompt history found")
            else:
                cfw.show_gpt_history(hist, gpt_allow_history_deletion)

        for message in st.session_state.gpt_messages:
            with st.chat_message(message['role']):
                st.markdown(message["content"])

        if prompt := st.chat_input("Enter your prompt"):
            # Display user message in chat message container
            with st.chat_message(role):
                st.markdown(prompt)

            if cf.isBlank(prompt) or len(prompt) < 5:
                st.error("Please provide a prompt of at least 5 characters before requesting an answer", icon="✋")
                return ()

            prompt = self.gpt_presets[presets]["pre"] + prompt + self.gpt_presets[presets]["post"]

            prompt_token_count = self.oaiwui_gpt.estimate_tokens(prompt)
            requested_token_count = prompt_token_count + max_tokens
            if requested_token_count > self.models[model_name]["context_token"]:
                st.warning("You requested an estimated %i tokens, which might exceed the model's context window of %i tokens. We are still proceeding with the request, but an error return is possible." % (requested_token_count, self.models[model_name]["context_token"]))

            if max_tokens > 0:
                tmp_txt1 = "" if tokens_selector is False else f" for max_tokens: {max_tokens}"
                tmp_txt2 = "" if temperature_selector is False else f" (temperature: {temperature})"
                st.toast(f"Requesting {model_provider} with model: {model_name}{tmp_txt1}{tmp_txt2}")
                with st.spinner(f"Asking {model_provider} with model: {model_name} {tmp_txt1}{tmp_txt2}. Prompt est. tokens : {prompt_token_count}"):
                    if msg_extra is None:
                        if 'gpt_msg_extra' in st.session_state:
                            msg_extra = st.session_state['gpt_msg_extra']
                    else:
                        if 'gpt_msg_extra' in st.session_state:
                            tmp = msg_extra
                            msg_extra = copy.deepcopy(st.session_state['gpt_msg_extra'])
                            msg_extra.append(tmp[0])

                    st.session_state.gpt_messages.append({"role": role, "content": prompt})

                    # only add the model to the list if it is different from the last one
                    if len(st.session_state.model_used) == 0 or st.session_state.model_used[-1] != model_name:
                        st.session_state.model_used.append(model_name)

                    err, run_file = self.oaiwui_gpt.chatgpt_it(model_name, st.session_state.gpt_messages, max_tokens, temperature, msg_extra, websearch, **self.gpt_presets[presets]["kwargs"])
                    if cf.isNotBlank(err):
                        st.error(err)
                    if cf.isNotBlank(run_file):
                        st.session_state[self.last_gpt_query] = run_file
                        st.toast("Done")

        if len(st.session_state.model_used) > 0:
            cf.logit(f"ℹ️ Models prompted: {', '.join(st.session_state.model_used)}", "info")

        if self.last_gpt_query in st.session_state:
            run_file = st.session_state[self.last_gpt_query]
            run_json = cf.get_run_file(run_file)

            response = run_json[-1]["content"]
            st.chat_message("assistant").write(response)
            st.session_state.gpt_messages.append({"role": "assistant", "content": response})
            del st.session_state[self.last_gpt_query]

        if download_placeholder is not None:
            chat_text = ""
            for msg in st.session_state.gpt_messages:
                chat_text += msg["role"] + ": " + msg["content"] + "\n"
            download_placeholder.download_button(label="Download Chat", data=chat_text)
