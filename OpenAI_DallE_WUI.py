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
import common_functions_WUI as cfw

from datetime import datetime

import OpenAI_DallE as OAI_DallE

##########
class OAI_DallE_WUI:
    def __init__(self, oai_dalle: OAI_DallE) -> None:
        self.last_gpt_query = "last_dalle_query"

        self.oai_dalle = oai_dalle
        self.save_location = oai_dalle.get_save_location()
        self.models = oai_dalle.get_models()
        self.model_help = oai_dalle.get_model_help()
        self.models_status = oai_dalle.get_models_status()
        self.per_model_help = oai_dalle.get_per_model_help()
        self.dalle_modes = oai_dalle.get_dalle_modes()

        self.last_dalle_query = oai_dalle.last_dalle_query


#####
    def get_dest_dir(self):
        return self.oai_dalle.get_dest_dir()

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
            st.text("Check the various ? for help", help=f"[Run Details]\n\nRunID: {cfw.get_runid()}\n\nSave location: {self.save_location}\n\nUTC time: {cf.get_timeUTC()}\n")
            mode = list(self.dalle_modes.keys())[0]
            if len(self.dalle_modes.keys()) > 1:
                mode = st.selectbox("mode", options=list(self.dalle_modes.keys()), index=0, key="dalle_mode", help=self.dalle_help)
            model = st.selectbox("model", options=list(self.models.keys()), index=0, key="model", help=self.model_help)
            if model in self.models_status:
                st.info(f"{model}: {self.models_status[model]}")
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

            dalle_show_tooltip = st.toggle(label="Show Tips", value=False, key="dalle_show_tooltip", help="Show tips on how to use this tool")
            dalle_show_history = st.toggle(label='Show Prompt History', value=False, help="Show a list of prompts that you have used in the past (most recent first). Loading a selected prompt does not load the parameters used for the generation.", key="dalle_show_history")
            if dalle_show_history:
                dalle_allow_history_deletion = st.toggle('Allow Prompt History Deletion', value=False, help="This will allow you to delete a prompt from the history. This will delete the prompt and all its associated files. This cannot be undone.", key="dalle_allow_history_deletion")


        if dalle_show_tooltip:
            stoggle(
                'Tips',
                'DALL·E is an AI system that creates realistic images and art from a description in natural language.<br>- The more detailed the description, the more likely you are to get the result that you or your end user want'
            )

        if dalle_show_history:
            err, hist = self.oai_dalle.get_history()
            if cf.isNotBlank(err):
                st.error(err)
                cf.error_exit(err)
            if len(hist) == 0:
                st.warning("No prompt history found")
            else:
                cfw.show_history(hist, dalle_allow_history_deletion, 'dalle_last_prompt', self.last_dalle_query)

        if 'dalle_last_prompt' not in st.session_state:
            st.session_state['dalle_last_prompt'] = ""
        prompt_value=f"DallE {model} Input [image size: {img_size} | image count: {img_count} | Extra: {kwargs}]"
        help_text = self.per_model_help[model] if model in self.per_model_help else "No help available for this model"
        prompt = st.empty().text_area(prompt_value, st.session_state["dalle_last_prompt"], placeholder="Enter your prompt", key="dalle_input", help=help_text)
        st.session_state['dalle_last_prompt'] = prompt

        if st.button("Submit Request", key="dalle_request_answer"):
            if cf.isBlank(prompt) or len(prompt) < 10:
                st.error("Please provide a prompt of at least 10 characters before requesting an answer", icon="✋")
                return ()
            if len(prompt) > self.models[model]["max_prompt_length"]:
                st.error(f"Your prompt is {len(prompt)} characters long, which is more than the maximum of {self.models[model]['max_prompt_length']} for this model")
                return ()
            
            dalle_dest_dir = self.get_dest_dir()
            st_placeholder = st.empty()
            with st.spinner(f"Asking OpenAI for a response..."):
                err, run_file = self.oai_dalle.dalle_it(model, prompt, img_size, img_count, dalle_dest_dir, st_placeholder, **kwargs)
                if cf.isNotBlank(err):
                    st.error(err)
                if cf.isNotBlank(run_file):
                    st.session_state[self.last_dalle_query] = run_file
                    st.toast("Done")

        if self.last_dalle_query in st.session_state:
            run_file = st.session_state[self.last_dalle_query]
            run_json = cf.get_run_file(run_file)
            self.display_dalle_images(run_json['prompt'], run_json['images'])