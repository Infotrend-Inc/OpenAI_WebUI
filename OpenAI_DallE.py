import openai
from openai import OpenAI

import streamlit as st
import extra_streamlit_components as stx
from streamlit_extras.stoggle import stoggle
from streamlit_image_select import image_select

import json

import requests

import os.path
import pathlib
import fnmatch

import common_functions as cf

from datetime import datetime


######
# https://github.com/openai/openai-openapi/blob/master/openapi.yaml
def dalle_call(apikey, model, prompt, img_size, img_count, **kwargs):
    client = OpenAI(api_key=apikey)

    # Generate a response
    try:
        response = client.images.generate(
            model=model,
            prompt=prompt,
            size=img_size,
            n=img_count,
            **kwargs
        )
    except openai.APIError as e:
        return(f"OpenAI API returned an API Error: {e}", "")
    except openai.APIConnectionError as e:
        return(f"OpenAI API request failed to connect: {e}", "")
    except openai.AuthenticationError as e:
        return(f"OpenAI API request was not authorized: {e}", "")
    except openai.RateLimitError as e:
        return(f"OpenAI API request exceeded rate limit: {e}", "")
    except openai.OpenAIError as e:
        return(f"OpenAI API request failed: {e}", "")

    return "", response


##########
class OAI_DallE:
    def __init__(self, apikey, save_location, models_list):
        self.last_dalle_query = 'last_dalle_query'

        self.apikey = apikey
        self.save_location = save_location

        self.models_supported = models_list
        self.set_parameters(models_list)

        self.dalle_modes = {
            "Image": "The image generations endpoint allows you to create an original image given a text prompt. Generated images and maximum number of requested images depends on the model selected. Smaller sizes are faster to generate."
        }
        self.dalle_help = ""
        for key in self.dalle_modes:
            self.dalle_help += key + ":\n"
            self.dalle_help += self.dalle_modes[key] + "\n"


#####
    def set_parameters(self, models_list):
        models = {}
        model_help = ""

        all = {
            "dall-e-2":
            {
                "label": "The previous DALL·E model released in Nov 2022. The maximum prompt length is 1000 characters.",
                "image_size": ["256x256", "512x512", "1024x1024"]
            },
            "dall-e-3":
            {
                "label": "The latest DALL·E model released in Nov 2023. The maximum prompt length is 4000 characters.",
                "image_size": ["1024x1024", "1024x1792", "1792x1024"]        
            }
        }

        s_models_list = models_list.split(",")
        known_models = list(all.keys())
        for t_model in s_models_list:
            model = t_model.strip()
            if model in all:
                models[model] = all[model]
            else:
                st.error(f"Unknown model: [{model}] | Known models: {known_models}")
                cf.error_exit(f"Unknown model {model}")

        model_help = ""
        for key in models:
            model_help += key + ":\n"
            model_help += models[key]["label"] + "\n"
            model_help += "image_size: " + str(models[key]["image_size"]) + "\n"

        self.models = models
        self.model_help = model_help


#####
    def get_dest_dir(self):
        return os.path.join(self.save_location, "dalle", cf.get_timeUTC())


#####
    def dalle_it(self, model, prompt, img_size, img_count, dest_dir, **kwargs):
        err = cf.check_existing_dir_w(dest_dir)
        if cf.isNotBlank(err):
            st.error(f"While checking {dest_dir}: {err}")
            cf.error_exit(err)

        err, response = dalle_call(self.apikey, model, prompt, img_size, img_count, **kwargs)
        if cf.isNotBlank(err):
            return err, ""

        info_placeholder = st.empty()
        all_images = []
        for i in range(img_count):
            image_name = f"{dest_dir}/{i + 1}.png"
            image_url = response.data[i].url
            info_placeholder.info(f"Downloading result {i + 1} as {image_name}")
            img_data = requests.get(image_url).content
            with open(image_name, 'wb') as handler:
                handler.write(img_data)
            all_images.append(image_name)
        info_placeholder.empty()

        runid = cf.get_runid()
        run_file = f"{dest_dir}/run---{runid}.json"
        run_json = {
            "prompt": prompt,
            "images": all_images,
        }
        with open(run_file, 'w') as f:
            json.dump(run_json, f, indent=4)

        return "", run_file


#####
    def display_dalle_images(self, prompt, all_images):
        img = image_select("Prompt: " + prompt, all_images, use_container_width=False)
        st.image(img)
        path = pathlib.PurePath(img)
        wdir = path.parent.name
        wfile = path.name
        dfile = f"{wdir}-{wfile}"
        st.download_button("Download Selected", data=open(img, 'rb').read(), file_name=dfile, mime="image/png", key="dalle_download_button")


#####
    def get_history(self):
        hist = {}
        search_dir = os.path.join(self.save_location, "dalle")
        err, listing = cf.get_dirlist(search_dir, "dalle save location")
        if cf.isNotBlank(err):
            st.error(f"While getting directory listing from {self.save_location}: {err}, history will be incomplete")
            return hist
        for entry in listing:
            entry_dir = os.path.join(search_dir, entry)
            err = cf.check_existing_dir_w(entry_dir)
            if cf.isNotBlank(err):
                st.error(f"While checking {entry_dir}: {err}, history will be incomplete")
                continue
            for file in os.listdir(entry_dir):
                if fnmatch.fnmatch(file, 'run---*.json'):
                    run_file = os.path.join(entry_dir, file)
                    run_json = cf.get_run_file(run_file)
                    if 'prompt' in run_json:
                        prompt = run_json['prompt']
                        hist[entry] = [prompt, run_file]
                    break
        return hist
    

#####
    def set_ui(self):
        st.sidebar.empty()
        with st.sidebar:
            st.text("Check the various ? for help", help=f"[Run Details]\n\nRunID: {cf.get_runid()}\n\nSave location: {self.save_location}\n\nUTC time: {cf.get_timeUTC()}\n")
            mode = st.selectbox("mode", options=list(self.dalle_modes.keys()), index=0, key="dalle_mode", help=self.dalle_help)
            model = st.selectbox("model", options=list(self.models.keys()), index=0, key="model", help=self.model_help)
            model_image_size = self.models[model]["image_size"]
            img_size = st.selectbox("image size", options=model_image_size, index=0, key="dalle_image_size",
                                    help="Smaller sizes are faster to generate.")

            if model == "dall-e-2":
                img_count = st.number_input("number of images", min_value=1, max_value=10, value=1, step=1, key="dalle_img_count",
                                            help="Number of images to generate.")
            else:
                img_count = 1

            kwargs = {}
            if model == "dall-e-3":
                quality = st.selectbox("quality", options=["standard", "hd"], index=0, key="dalle_quality", help="The quality of the image that will be generated. hd creates images with finer details and greater consistency across the image.")
                style = st.selectbox("style", options=["vivid", "natural"], index=0, key="dalle_style", help="The style of the generated images. Vivid causes the model to lean towards generating hyper-real and dramatic images. Natural causes the model to produce more natural, less hyper-real looking images.")
                kwargs = {"quality": quality, "style": style}

            show_tooltip = st.toggle(label="Show Tips", value=True, key="dalle_show_tooltip", help="Show tips on how to use this tool")
            show_history = st.toggle(label='Show Prompt History', value=False, help="Show a list of prompts that you have used in the past (most recent first). Loading a selected prompt does not load the parameters used for the generation.", key="dalle_show_history")
            if show_history:
                allow_history_deletion = st.toggle('Allow Prompt History Deletion', value=False, help="This will allow you to delete a prompt from the history. This will delete the prompt and all its associated files. This cannot be undone.", key="dalle_allow_history_deletion")


        if show_tooltip:
            stoggle(
                'Tips',
                'DALL·E is an AI system that creates realistic images and art from a description in natural language.<br>- The more detailed the description, the more likely you are to get the result that you or your end user want'
            )

        if show_history:
            hist = self.get_history()
            hk = [x for x in hist.keys() if cf.isNotBlank(x)]
            hk = sorted(hk, reverse=True)
            hk_opt = [hist[x][0] for x in hk]
            hk_q = {hist[x][0]: hist[x][1] for x in hk}
            prev = st.selectbox("Prompt History (most recent first)", options=hk_opt, index=0, key="history")
            if st.button("Load Selected Prompt", key="load_history"):
                st.session_state['dalle_last_prompt'] = prev
                st.session_state[self.last_dalle_query] = hk_q[prev]
            if allow_history_deletion:
                if st.button("Delete Selected Prompt", key="delete_history"):
                    if cf.isNotBlank(prev):
                        dir = os.path.dirname(hk_q[prev])
                        err = cf.directory_rmtree(dir)
                        if cf.isNotBlank(err):
                            st.error(f"While deleting {dir}: {err}")
                        else:
                            if os.path.exists(dir):
                                st.error(f"Directory {dir} still exists")
                            else:
                                st.success(f"Deleted")
                    else:
                        st.error("Please select a prompt to delete")

        if 'dalle_last_prompt' not in st.session_state:
            st.session_state['dalle_last_prompt'] = ""
        prompt_value=f"DallE {model} Input [image size: {img_size} | image count: {img_count} | Extra: {kwargs}]"
        prompt = st.empty().text_area(prompt_value, st.session_state["dalle_last_prompt"], placeholder="Enter your prompt", key="dalle_input")
        st.session_state['dalle_last_prompt'] = prompt

        if st.button("Submit Request", key="dalle_request_answer"):
            if cf.isBlank(prompt) or len(prompt) < 10:
                st.error("Please provide a prompt of at least 10 characters before requesting an answer", icon="✋")
                return ()

            dalle_dest_dir = self.get_dest_dir()
            
            cf.make_wdir_error(dalle_dest_dir)
            with st.spinner(f"Asking OpenAI for a response..."):
                err, run_file = self.dalle_it(model, prompt, img_size, img_count, dalle_dest_dir, **kwargs)
                if cf.isNotBlank(err):
                    st.error(err)
                if cf.isNotBlank(run_file):
                    st.session_state[self.last_dalle_query] = run_file
                    st.toast("Done")

        if self.last_dalle_query in st.session_state:
            run_file = st.session_state[self.last_dalle_query]
            run_json = cf.get_run_file(run_file)
            self.display_dalle_images(run_json['prompt'], run_json['images'])