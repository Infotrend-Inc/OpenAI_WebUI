#!/usr/bin/env python3

# Based on 
# https://platform.openai.com/docs/quickstart/build-your-application
# https://github.com/openai/openai-python

import streamlit as st
import extra_streamlit_components as stx

from OpenAI_GPT import OAI_GPT
from OpenAI_DallE import OAI_DallE

from OpenAI_GPT_WUI import OAI_GPT_WUI
from OpenAI_DallE_WUI import OAI_DallE_WUI

import re
import os.path

import common_functions as cf

from dotenv import load_dotenv
from datetime import datetime

import hmac

#####
iti_version=cf.iti_version

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
# https://docs.streamlit.io/knowledge-base/deploy/authentication-without-sso
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "WebUI Required Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False


#####
def main():
    # Load all supported models (need the status field to decide or prompt if we can use that model or not)
    av_gpt_models, av_dalle_models = load_models()    

    err = cf.check_file_r(".streamlit/secrets.toml", "Secrets file")
    if cf.isBlank(err):
        if not check_password():
            st.error("Required password incorrect, can not continue")
            st.stop()

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

    gpt_vision = True
    if 'OAIWUI_GPT_VISION' in os.environ:
        tmp = os.environ.get('OAIWUI_GPT_VISION')
        if tmp.lower() == "false":
            gpt_vision = False
        elif tmp.lower() == "true" :
            gpt_vision = True
        else:
            st.error(f"OAIWUI_GPT_VISION environment variable must be set to 'True' or 'False'")
            cf.error_exit("OAIWUI_GPT_VISION environment variable must be set to 'True' or 'False'")

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

    prompt_presets_dir = None
    if 'OAIWUI_PROMPT_PRESETS_DIR' in os.environ:
        tmp = os.environ.get('OAIWUI_PROMPT_PRESETS_DIR')
        if cf.isBlank(tmp):
            st.warning(f"OAIWUI_PROMPT_PRESETS_DIR provided but empty, will not use prompt presets")

        else:
            err = cf.check_dir(tmp, "OAIWUI_PROMPT_PRESETS_DIR directory")
            if cf.isNotBlank(err):
                st.warning(f"While checking OAIWUI_PROMPT_PRESETS_DIR: {err}")
            else:
                has_json = False
                for file in os.listdir(tmp):
                    if file.endswith(".json"):
                        has_json = True
                        break
                if not has_json:
                    st.warning(f"OAIWUI_PROMPT_PRESETS_DIR provided but appears to not contain prompts, will not use prompt presets")
                else: # all the conditions are met
                    prompt_presets_dir = tmp

    prompt_presets_file = None 
    if 'OAIWUI_PROMPT_PRESETS_ONLY' in os.environ:
        tmp = os.environ.get('OAIWUI_PROMPT_PRESETS_ONLY')
        if cf.isBlank(tmp):
            st.warning(f"OAIWUI_PROMPT_PRESETS_ONLY provided but empty, will not use prompt presets")
        else:
            err = cf.check_file_r(tmp)
            if cf.isNotBlank(err):
                st.warning(f"While checking OAIWUI_PROMPT_PRESETS_ONLY: {err}")
            else:
                if prompt_presets_dir is None:
                    st.warning(f"OAIWUI_PROMPT_PRESETS_ONLY provided but no OAIWUI_PROMPT_PRESETS_DIR, will not use prompt presets")
                else: # all the conditions are met
                    prompt_presets_file = tmp

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
        long_save_location = os.path.join(save_location, iti_version)
        cf.make_wdir_error(os.path.join(long_save_location))

        set_ui(long_save_location, username, apikey, gpt_models, av_gpt_models, gpt_vision, dalle_models, av_dalle_models, prompt_presets_dir, prompt_presets_file)

#####

def process_error_warning(err, warn):
    if cf.isNotBlank(err):
        st.error(err)
        cf.error_exit(err)
    if cf.isNotBlank(warn):
        st.warning(warn)


#####

def set_ui(long_save_location, username, apikey, gpt_models, av_gpt_models, gpt_vision, dalle_models, av_dalle_models, prompt_presets_dir: str = None, prompt_presets_file: str = None):
    oai_gpt = OAI_GPT(apikey, long_save_location, username)
    err, warn = oai_gpt.set_parameters(gpt_models, av_gpt_models)
    process_error_warning(err, warn)
    oai_gpt_st = OAI_GPT_WUI(oai_gpt, gpt_vision, prompt_presets_dir, prompt_presets_file)
    oai_dalle = None
    oai_dalle_st = None
    if 'OAIWUI_GPT_ONLY' in os.environ:
        tmp = os.environ.get('OAIWUI_GPT_ONLY')
        if tmp.lower() == "true":
            oai_dalle = None
        elif tmp.lower() == "false":
            oai_dalle = OAI_DallE(apikey, long_save_location, username)
            err, warn = oai_dalle.set_parameters(dalle_models, av_dalle_models)
            process_error_warning(err, warn)
            oai_dalle_st = OAI_DallE_WUI(oai_dalle)
#            dalle_process_error_warning_info(oai_dalle)
        else:
            st.error(f"OAIWUI_GPT_ONLY environment variable must be set to 'True' or 'False'")
            cf.error_exit("OAIWUI_GPT_ONLY environment variable must be set to 'True' or 'False'")

    if oai_dalle is None:
        oai_gpt_st.set_ui()
    else:
        chosen_id = stx.tab_bar(data=[
            stx.TabBarItemData(id="gpt_tab", title="GPT", description="Text generation using OpenAI's GPT"),
            stx.TabBarItemData(id="dalle_tab", title="Dall-E", description="Image generation using OpenAI's Dall-E")
            ])
        if chosen_id == "dalle_tab":
            oai_dalle_st.set_ui()
        else:
            oai_gpt_st.set_ui()


#####
if __name__ == "__main__":
    main()
