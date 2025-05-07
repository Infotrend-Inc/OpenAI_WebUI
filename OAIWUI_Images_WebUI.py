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

import common_functions as cf
import common_functions_WebUI as cfw

from datetime import datetime

import OAIWUI_Images as OAIWUI_Images

##########
class OAIWUI_Images_WebUI:
    def __init__(self, oaiwui_images: OAIWUI_Images) -> None:
        self.last_images_query = "last_images_query"

        self.oaiwui_images = oaiwui_images
        self.save_location = oaiwui_images.get_save_location()
        self.models = oaiwui_images.get_models()
        self.model_help = oaiwui_images.get_model_help()
        self.models_status = oaiwui_images.get_models_status()
        self.per_model_help = oaiwui_images.get_per_model_help()
        self.images_modes = oaiwui_images.get_images_modes()

        self.models_warning = oaiwui_images.get_models_warning()
        self.known_models = oaiwui_images.get_known_models()

        self.last_images_query = oaiwui_images.last_images_query


#####
    def get_dest_dir(self):
        return self.oaiwui_images.get_dest_dir()

#####
    def display_images(self, prompt, all_images):
        img = image_select("Prompt: " + prompt, all_images, use_container_width=False)
        st.image(img)
        path = pathlib.PurePath(img)
        wdir = path.parent.name
        wfile = path.name
        dfile = f"{wdir}-{wfile}"
        st.download_button("Download Selected", data=open(img, 'rb').read(), file_name=dfile, mime="image/png", key="images_download_button")

#####
    def set_ui(self):
        st.sidebar.empty()
        with st.sidebar:
            st.text("Check the various ? for help", help=f"[Run Details]\n\nRunID: {cfw.get_runid()}\n\nSave location: {self.save_location}\n\nUTC time: {cf.get_timeUTC()}\n")
            mode = list(self.images_modes.keys())[0]
            if len(self.images_modes.keys()) > 1:
                mode = st.selectbox("mode", options=list(self.images_modes.keys()), index=0, key="images_mode", help=self.images_help)
            model = st.selectbox("model", options=list(self.models.keys()), index=0, key="model", help=self.model_help)
            if model in self.models_status:
                st.info(f"{model}: {self.models_status[model]}")
            model_image_size = self.models[model]["image_size"]
            img_size = st.selectbox("image size", options=model_image_size, index=0, key="images_image_size",
                                    help="Smaller sizes are faster to generate.")

            if model == "dall-e-2":
                img_count = st.number_input("number of images", min_value=1, max_value=10, value=1, step=1, key="images_img_count",
                                            help="Number of images to generate.")
            else:
                img_count = 1

            kwargs = {}
            quality_options = []
            if 'quality' in self.models[model]['meta']:
                quality_options = self.models[model]['meta']['quality']
            style_options = []
            if 'style' in self.models[model]['meta']:
                style_options = self.models[model]['meta']['style']

            if quality_options:
                quality = st.selectbox("quality", options=quality_options, index=0, key="images_quality", help="The quality of the image that will be generated. hd creates images with finer details and greater consistency across the image.")
                kwargs['quality'] = quality
            if style_options:
                style = st.selectbox("style", options=style_options, index=0, key="images_style", help="The style of the generated images. Vivid causes the model to lean towards generating hyper-real and dramatic images. Natural causes the model to produce more natural, less hyper-real looking images.")
                kwargs['style'] = style

            if 'transparent' in self.models[model]['meta']:
                transparent = st.toggle("transparent", value=False, key="images_transparent", help="If enabled, the image will be generated with a transparent background.")
                if transparent:
                    kwargs['background'] = "transparent"

            images_show_history = st.toggle(label='Show Prompt History', value=False, help="Show a list of prompts that you have used in the past (most recent first). Loading a selected prompt does not load the parameters used for the generation.", key="images_show_history")
            if images_show_history:
                images_allow_history_deletion = st.toggle('Allow Prompt History Deletion', value=False, help="This will allow you to delete a prompt from the history. This will delete the prompt and all its associated files. This cannot be undone.", key="images_allow_history_deletion")

            # Check for model warnings
            if list(self.models_warning.keys()) != []:
                warning_text = " - " +"\n - ".join ([f"{model}: {self.models_warning[model]}" for model in sorted(self.models_warning.keys())])
                warning_text += f"\n\n\nKnown models: {self.known_models}"
                st.text("⚠️ Models warnings", help=f"{warning_text}")

        if images_show_history:
            err, hist = self.oaiwui_images.get_history()
            if cf.isNotBlank(err):
                st.error(err)
                cf.error_exit(err)
            if len(hist) == 0:
                st.warning("No prompt history found")
            else:
                cfw.show_history(hist, images_allow_history_deletion, 'images_last_prompt', self.last_images_query)

        if 'images_last_prompt' not in st.session_state:
            st.session_state['images_last_prompt'] = ""
        prompt_value=f"Images {model} Input [image size: {img_size} | image count: {img_count} | Extra: {kwargs}]"
        help_text = '\n\nDALL·E is an AI system that creates realistic images and art from a description in natural language.\n\n- The more detailed the description, the more likely you are to get the result that you or your end user want'
        prompt = st.empty().text_area(prompt_value, st.session_state["images_last_prompt"], placeholder="Enter your prompt", key="images_input", help=help_text)
        st.session_state['images_last_prompt'] = prompt

        if st.button("Submit Request", key="images_request_answer"):
            if cf.isBlank(prompt) or len(prompt) < 10:
                st.error("Please provide a prompt of at least 10 characters before requesting an answer", icon="✋")
                return ()
            if len(prompt) > self.models[model]["max_prompt_length"]:
                st.error(f"Your prompt is {len(prompt)} characters long, which is more than the maximum of {self.models[model]['max_prompt_length']} for this model")
                return ()
            
            images_dest_dir = self.get_dest_dir()
            with st.spinner(f"Asking OpenAI for a response..."):
                err, warn, run_file = self.oaiwui_images.images_it(model, prompt, img_size, img_count, images_dest_dir, **kwargs)
                if cf.isNotBlank(err):
                    st.error(err)
                if cf.isNotBlank(warn):
                    st.warning(warn)
                if cf.isNotBlank(run_file):
                    st.session_state[self.last_images_query] = run_file
                    st.toast("Done")

        if self.last_images_query in st.session_state:
            run_file = st.session_state[self.last_images_query]
            run_json = cf.get_run_file(run_file)
            self.display_images(run_json['prompt'], run_json['images'])