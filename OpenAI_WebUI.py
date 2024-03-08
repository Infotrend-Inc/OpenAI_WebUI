#!/usr/bin/env python3

# Based on 
# https://platform.openai.com/docs/quickstart/build-your-application
# https://github.com/openai/openai-python

import streamlit as st
import extra_streamlit_components as stx
from OpenAI_GPT import OAI_GPT
from OpenAI_DallE import OAI_DallE

import re
import os.path

import common_functions as cf

from dotenv import load_dotenv
from datetime import datetime

#####
iti_version="0.9.2"
st.set_page_config(page_title=f"OpenAI API WebUI ({iti_version})", page_icon="🫥", layout="wide", initial_sidebar_state="expanded", menu_items={'Get Help': 'https://github.com/Infotrend-Inc/OpenAI_WebUI', 'About': f"# OpenAI WebUI ({iti_version})\n Brought to you by [Infotrend Inc.](https://www.infotrend.com/)"})

#####
def load_models():
    err = cf.check_file_r("models.json", "models.json")
    if cf.isNotBlank(err):
        st.error(f"While checking models.json: {err}")
        cf.error_exit(f"While checking models.json: {err}")
    all_models = cf.read_json("models.json")
    if all_models is None:
        st.error(f"Could not read models.json")
        cf.error_exit(f"Could not read models.json")
    gpt_models = {}
    if 'GPT' in all_models:
        gpt_models = all_models['GPT']
    else:
        st.error(f"Could not find GPT in models.json")
        cf.error_exit(f"Could not find GPT in models.json")
    dalle_models = {}
    if 'DallE' in all_models:
        dalle_models = all_models['DallE']
    else:
        st.error(f"Could not find DallE in models.json")
        cf.error_exit(f"Could not find DallE in models.json")
    return gpt_models, dalle_models

#####
def main():
    # Load all supported models (need the status field to decide or prompt if we can use that model or not)
    av_gpt_models, av_dalle_models = load_models()    

    err = cf.check_file_r(".env", "Environment file")
    if cf.isBlank(err):
        load_dotenv()
    # If the file is not present, hopefully the variable was set in the Docker environemnt

    apikey = ''
    if 'OPENAI_API_KEY' in os.environ:
        apikey = os.environ.get('OPENAI_API_KEY')
    if cf.isBlank(apikey):
        st.error(f"Could not find the OPENAI_API_KEY environment variable")
        cf.error_exit(f"Could not find the OPENAI_API_KEY environment variable")
    
    save_location = ""
    if 'OAIWUI_SAVEDIR' in os.environ:
        save_location = os.environ.get('OAIWUI_SAVEDIR')
    if cf.isBlank(save_location):
        st.error(f"Could not find the OAIWUI_SAVEDIR environment variable")
        cf.error_exit("Could not find the OAIWUI_SAVEDIR environment variable")
    err = cf.check_existing_dir_w(save_location, "OAIWUI_SAVEDIR directory")
    if cf.isNotBlank(err):
        st.error(f"While checking OAIWUI_SAVEDIR: {err}")
        cf.error_exit(f"{err}")

    gpt_models = ""
    if 'OAIWUI_GPT_MODELS' in os.environ:
        gpt_models = os.environ.get('OAIWUI_GPT_MODELS')
    else:
        st.error(f"Could not find the OAIWUI_GPT_MODELS environment variable")
        cf.error_exit("Could not find the OAIWUI_GPT_MODELS environment variable")
    if cf.isBlank(gpt_models):
        st.error(f"OAIWUI_GPT_MODELS environment variable is empty")
        cf.error_exit("OAIWUI_GPT_MODELS environment variable is empty")

    dalle_models = ""
    if 'OAIWUI_DALLE_MODELS' in os.environ:
        dalle_models = os.environ.get('OAIWUI_DALLE_MODELS')
    else:
        st.error(f"Could not find the OAIWUI_DALLE_MODELS environment variable")
        cf.error_exit("Could not find the OAIWUI_DALLE_MODELS environment variable")
    if cf.isBlank(dalle_models):
        st.error(f"OAIWUI_DALLE_MODELS environment variable is empty")
        cf.error_exit("OAIWUI_DALLE_MODELS environment variable is empty")

    username = ""
    if 'OAIWUI_USERNAME' in os.environ:
        username = os.environ.get('OAIWUI_USERNAME')
        if cf.isBlank(username):
            st.warning(f"OAIWUI_USERNAME provided but empty, will ask for username")
        else:
            st.session_state['username'] = username

    # Store the initial value of widgets in session state
    if "visibility" not in st.session_state:
        st.session_state.visibility = "visible"
        st.session_state.disabled = False

    if 'webui_runid' not in st.session_state:
        st.session_state['webui_runid'] = datetime.now().strftime("%Y%m%d-%H%M%S")

    st.empty()

    # Grab a session-specific value for username
    username = ""
    if 'username' in st.session_state:
        username = st.session_state['username']
    
    if cf.isBlank(username):
        st.image("./assets/Infotrend_Logo.png", width=600)
        username = st.text_input("Enter a username (unauthorized characters will be replaced by _)")
        if st.button("Save username"):
            # replace non alphanumeric by _
            username = re.sub('[^0-9a-zA-Z]+', '_', username)
            if cf.isBlank(username):
                st.error(f"Username cannot be empty")
            else:
                st.session_state['username'] = username
                st.rerun()
    else:
        cf.make_wdir_error(os.path.join(save_location))
        cf.make_wdir_error(os.path.join(save_location, iti_version))
        long_save_location = os.path.join(save_location, iti_version, username)
        cf.make_wdir_error(os.path.join(long_save_location))
        cf.make_wdir_error(os.path.join(long_save_location, "dalle"))
        cf.make_wdir_error(os.path.join(long_save_location, "gpt"))

        set_ui(long_save_location, apikey, gpt_models, av_gpt_models, dalle_models, av_dalle_models)


#####
def set_ui(long_save_location, apikey, gpt_models, av_gpt_models, dalle_models, av_dalle_models):
    oai_gpt = OAI_GPT(apikey, long_save_location, gpt_models, av_gpt_models)
    oai_dalle = None
    if 'OAIWUI_GPT_ONLY' in os.environ:
        tmp = os.environ.get('OAIWUI_GPT_ONLY')
        if tmp == "True":
            oai_dalle = None
        elif tmp == "False":
            oai_dalle = OAI_DallE(apikey, long_save_location, dalle_models, av_dalle_models)
        else:
            st.error(f"OAIWUI_GPT_ONLY environment variable must be set to 'True' or 'False'")
            cf.error_exit("OAIWUI_GPT_ONLY environment variable must be set to 'True' or 'False'")

    if oai_dalle is None:
        oai_gpt.set_ui()
    else:
        chosen_id = stx.tab_bar(data=[
            stx.TabBarItemData(id="gpt_tab", title="GPT", description="Text generation using OpenAI's GPT"),
            stx.TabBarItemData(id="dalle_tab", title="Dall-E", description="Image generation using OpenAI's Dall-E")
            ])
        if chosen_id == "dalle_tab":
            oai_dalle.set_ui()
        else:
            oai_gpt.set_ui()


#####
if __name__ == "__main__":
    main()
