import openai
from openai import OpenAI

import streamlit as st
import extra_streamlit_components as stx
from streamlit_toggle import st_toggle_switch
from streamlit_extras.stoggle import stoggle
from streamlit_image_select import image_select

import json

import requests

import os.path
import pathlib

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
            "Image": "The image generations endpoint allows you to create an original image given a text prompt. Generated images can have a size of 256x256, 512x512, or 1024x1024 pixels. Smaller sizes are faster to generate. You can request 1-10 images at a time using the n parameter."
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
        request_time = datetime.today().isoformat()
        return os.path.join(self.save_location, "dalle", request_time)


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
    def set_ui(self):
        st.sidebar.empty()
        with st.sidebar:
            st.text("Please check the ? for help")
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

            show_tooltip = st_toggle_switch(label="Show Tips", key="show_tips", default_value=True, label_after=False)

        if show_tooltip:
            stoggle(
                'Tips',
                'DALL·E is an AI system that creates realistic images and art from a description in natural language.<br>- The more detailed the description, the more likely you are to get the result that you or your end user want'
            )

        prompt_value=f"DallE {model} Input [image size: {img_size} | image count: {img_count} | Extra: {kwargs}]"
        prompt = st.empty().text_area(prompt_value, "", placeholder="Enter your prompt", key="dalle_input")

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
                    st.session_state['last_dalle_query'] = run_file
                    st.toast("Done")

        if self.last_dalle_query in st.session_state:
            run_file = st.session_state[self.last_dalle_query]
            run_json = cf.get_run_file(run_file)
            self.display_dalle_images(run_json['prompt'], run_json['images'])