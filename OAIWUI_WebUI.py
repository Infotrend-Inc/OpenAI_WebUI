#!/usr/bin/env python3

import streamlit as st
import extra_streamlit_components as stx

from OAIWUI_GPT import OAIWUI_GPT
from OAIWUI_Images import OAIWUI_Images

from OAIWUI_GPT_WebUI import OAIWUI_GPT_WebUI
from OAIWUI_Images_WebUI import OAIWUI_Images_WebUI

import re
import os.path

import common_functions as cf
import ollama_helper as oll

from dotenv import load_dotenv
from datetime import datetime
import time

import hmac

#####
iti_version=cf.iti_version

st.set_page_config(page_title=f"OpenAI API Compatible WebUI ({iti_version})", page_icon="🫥", layout="wide", initial_sidebar_state="expanded", menu_items={'Get Help': 'https://github.com/Infotrend-Inc/OpenAI_WebUI', 'About': f"# OpenAI API Compatible WebUI ({iti_version})\n Brought to you by [Infotrend Inc.](https://www.infotrend.com/)"})

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

@st.cache_data
def get_ui_params(runid):
    cf.logit(f"---------- Main get_ui_params ({runid}) ----------", "debug")
    # Load all supported models (need the status field to decide or prompt if we can use that model or not)
    err, av_gpt_models, av_image_models = cf.load_models()    
    if cf.isNotBlank(err):
        st.error(err)
        cf.error_exit(err)

    warnings = [ ]

    err = cf.check_file_r(".env", "Environment file")
    if cf.isBlank(err):
        load_dotenv()
    # If the file is not present, hopefully the variable was set in the Docker environemnt

    # Deffering apikey check to the GPT class

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

    # Support old DALLE_MODELS environment variable
    if 'OAIWUI_DALLE_MODELS' in os.environ:
        if 'OAIWUI_IMAGE_MODELS' not in os.environ or cf.isBlank(os.environ.get('OAIWUI_IMAGE_MODELS')):
            warnings.append(f"OAIWUI_DALLE_MODELS environment variable is set but OAIWUI_IMAGE_MODELS is not set, will use OAIWUI_DALLE_MODELS as OAIWUI_IMAGE_MODELS. Please set OAIWUI_IMAGE_MODELS to avoid this warning")
            os.environ['OAIWUI_IMAGE_MODELS'] = os.environ.get('OAIWUI_DALLE_MODELS')

    image_models = ""
    if 'OAIWUI_IMAGE_MODELS' in os.environ:
        image_models = os.environ.get('OAIWUI_IMAGE_MODELS')
        if cf.isBlank(image_models):
            st.error(f"OAIWUI_IMAGE_MODELS environment variable is empty")
            cf.error_exit("OAIWUI_IMAGE_MODELS environment variable is empty")
    else:
        warnings.append(f"Disabling Images -- Could not find the OAIWUI_IMAGE_MODELS environment variable")
        os.environ['OAIWUI_GPT_ONLY'] = "True"

    if 'OLLAMA_HOST' in os.environ:
        OLLAMA_HOST = os.environ.get('OLLAMA_HOST')
        err, ollama_models = oll.get_all_ollama_models_and_infos(OLLAMA_HOST)
        if cf.isNotBlank(err):
            warnings.append(f"Disabling OLLAMA -- While testing OLLAMA_HOST {OLLAMA_HOST}: {err}")
        else:
            for oll_model in ollama_models:
                # We are going to extend the GPT models with the Ollama models
                err, modeljson = oll.ollama_to_modelsjson(OLLAMA_HOST, oll_model, ollama_models[oll_model])
                if cf.isNotBlank(err):
                    warnings.append(f"Disalbing OLLAMA model -- while obtaining OLLAMA model {oll_model} details: {err}")
                    continue
                av_gpt_models[oll_model] = modeljson
                gpt_models += f" {oll_model}"

    # variable to not fail on empy values, and just ignore those type of errors
    ignore_empty = False
    if 'OAIWUI_IGNORE_EMPTY' in os.environ: # values does not matter, just need to be present
        ignore_empty = True

    username = ""
    if 'OAIWUI_USERNAME' in os.environ:
        username = os.environ.get('OAIWUI_USERNAME')
        if cf.isBlank(username):
            if not ignore_empty:
                warnings.append(f"OAIWUI_USERNAME provided but empty, will ask for username")
        else:
            st.session_state['username'] = username

    prompt_presets_dir = None
    if 'OAIWUI_PROMPT_PRESETS_DIR' in os.environ:
        tmp = os.environ.get('OAIWUI_PROMPT_PRESETS_DIR')
        if cf.isBlank(tmp):
            if not ignore_empty:
                warnings.append(f"OAIWUI_PROMPT_PRESETS_DIR provided but empty, will not use prompt presets")

        else:
            err = cf.check_dir(tmp, "OAIWUI_PROMPT_PRESETS_DIR directory")
            if cf.isNotBlank(err):
                warnings.append(f"While checking OAIWUI_PROMPT_PRESETS_DIR: {err}")
            else:
                has_json = False
                for file in os.listdir(tmp):
                    if file.endswith(".json"):
                        has_json = True
                        break
                if not has_json:
                    warnings.append(f"OAIWUI_PROMPT_PRESETS_DIR provided but appears to not contain prompts, will not use prompt presets")
                else: # all the conditions are met
                    prompt_presets_dir = tmp

    prompt_presets_file = None 
    if 'OAIWUI_PROMPT_PRESETS_ONLY' in os.environ:
        tmp = os.environ.get('OAIWUI_PROMPT_PRESETS_ONLY')
        if cf.isBlank(tmp):
            if not ignore_empty:
                warnings.append(f"OAIWUI_PROMPT_PRESETS_ONLY provided but empty, will not use prompt presets")

        else:
            err = cf.check_file_r(tmp)
            if cf.isNotBlank(err):
                warnings.append(f"While checking OAIWUI_PROMPT_PRESETS_ONLY: {err}")
            else:
                if prompt_presets_dir is None:
                    warnings.append(f"OAIWUI_PROMPT_PRESETS_ONLY provided but no OAIWUI_PROMPT_PRESETS_DIR, will not use prompt presets")
                else: # all the conditions are met
                    prompt_presets_file = tmp

    # Store the initial value of widgets in session state
    if "visibility" not in st.session_state:
        st.session_state.visibility = "visible"
        st.session_state.disabled = False

    # Debug
    cf.logit(f"---------- get_ui_params ({runid}) ----------\nwarnings: {warnings}\nsave_location: {save_location}\ngpt_models: {gpt_models}\nav_gpt_models: {av_gpt_models}\ngpt_vision: {gpt_vision}\nimage_models: {image_models}\nav_image_models: {av_image_models}\nprompt_presets_dir: {prompt_presets_dir}\nprompt_presets_file: {prompt_presets_file}", "debug")

    return warnings, save_location, gpt_models, av_gpt_models, gpt_vision, image_models, av_image_models, prompt_presets_dir, prompt_presets_file


#####

@st.cache_data
def set_ui_core(long_save_location, username, gpt_models, av_gpt_models, gpt_vision, image_models, av_image_models, prompt_presets_dir: str = None, prompt_presets_file: str = None):
    oaiwui_gpt = OAIWUI_GPT(long_save_location, username)
    err, warn = oaiwui_gpt.set_parameters(gpt_models, av_gpt_models)
    process_error_warning(err, warn)
    oaiwui_gpt_st = OAIWUI_GPT_WebUI(oaiwui_gpt, gpt_vision, prompt_presets_dir, prompt_presets_file)
    oaiwui_images = None
    oaiwui_images_st = None
    if 'OAIWUI_GPT_ONLY' in os.environ:
        tmp = os.environ.get('OAIWUI_GPT_ONLY')
        if tmp.lower() == "true":
            oaiwui_images = None
        elif tmp.lower() == "false":
            oaiwui_images = OAIWUI_Images(long_save_location, username)
            err, warn = oaiwui_images.set_parameters(image_models, av_image_models)
            process_error_warning(err, warn)
            oaiwui_images_st = OAIWUI_Images_WebUI(oaiwui_images)
        else:
            st.error(f"OAIWUI_GPT_ONLY environment variable must be set to 'True' or 'False'")
            cf.error_exit("OAIWUI_GPT_ONLY environment variable must be set to 'True' or 'False'")

    return oaiwui_gpt, oaiwui_gpt_st, oaiwui_images, oaiwui_images_st


#####
def main():
    cf.logit("---------- Main __main__ ----------", "debug")

    err = cf.check_file_r(".streamlit/secrets.toml", "Secrets file")
    if cf.isBlank(err):
        if not check_password():
            st.error("Required password incorrect, can not continue")
            st.stop()

    if 'webui_runid' not in st.session_state:
        st.session_state['webui_runid'] = datetime.now().strftime("%Y%m%d-%H%M%S")

    warnings, save_location, gpt_models, av_gpt_models, gpt_vision, images_models, av_image_models, prompt_presets_dir, prompt_presets_file = get_ui_params(st.session_state['webui_runid'])

    if len(warnings) > 0:
        if 'warning_shown' not in st.session_state:
            phl = []
            for w in warnings:
                ph = st.empty()
                ph.warning(w)
                phl.append(ph)
            st.session_state['warning_shown'] = True
            time.sleep(7)
            for ph in phl:
                ph.empty()

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

        oaiwui_gpt, oaiwui_gpt_st, oaiwui_images, oaiwui_images_st = set_ui_core(long_save_location, username, gpt_models, av_gpt_models, gpt_vision, images_models, av_image_models, prompt_presets_dir, prompt_presets_file)

        set_ui(oaiwui_gpt, oaiwui_gpt_st, oaiwui_images, oaiwui_images_st)

#####

def process_error_warning(err, warn):
    if cf.isNotBlank(warn):
        cf.logit(warn, "warning")
    if cf.isNotBlank(err):
        if cf.isNotBlank(warn):
            st.warning(warn)
        st.error(err)
        cf.error_exit(err)


def set_ui(oaiwui_gpt, oaiwui_gpt_st, oaiwui_images, oaiwui_images_st):
    if oaiwui_images is None:
        oaiwui_gpt_st.set_ui()
    else:
        chosen_id = stx.tab_bar(data=[
            stx.TabBarItemData(id="gpt_tab", title="GPTs", description=""),
            stx.TabBarItemData(id="images_tab", title="Images", description="")
            ])
        if chosen_id == "images_tab":
            oaiwui_images_st.set_ui()
        else:
            oaiwui_gpt_st.set_ui()

def is_streamlit_running():
    try:
        # Check if we're running inside a Streamlit script
        return st.runtime.exists()
    except:
        return False

#####
if __name__ == "__main__":
    if is_streamlit_running():
        main()
    else:
        # start streamlit with all the command line arguments
        import subprocess
        import sys
        subprocess.call(["streamlit", "run"] + sys.argv[0:])
