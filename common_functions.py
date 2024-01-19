import os
import os.path
import pathlib
import sys
import shutil
import fnmatch

import streamlit as st

import json

from datetime import datetime

def isBlank (myString):
    return not (myString and myString.strip())

def isNotBlank (myString):
    return bool(myString and myString.strip())

#####

def get_fullpath(path):
    return(os.path.abspath(path))

#####

def check_file(file, text="checked file"):
    if not os.path.exists(file):
        return(text + " (" + file + ") does not exist")
    if not os.path.isfile(file):
        return(text + " (" + file + ") is not a file")
    return("")

##

def check_file_r(file, text="checked file"):
    err = check_file(file, text)
    if isNotBlank(err):
        return(err)
    if not os.access(file, os.R_OK):
        return(text + " (" + file + ") can not be read")
    return("")

##

def check_existing_file_w(file, text="checked file"):
    err = check_file(file, text)
    if isNotBlank(err):
        return(err)
    if not os.access(file, os.W_OK):
        return(text + " (" + file + ") can not be written to")
    return("")

##

def check_file_w(file, text="checked file"):
    try:
        with open(file, 'a') as f:
            return("")
    except IOError as x:
        return("Issue opening "+text+" file ("+file+") for writing : "+x.strerror)

##

def check_file_size(file, text="checked file"):
    err = check_file_r(file, text)
    if isNotBlank(err):
        return(err, 0)
    return("", pathlib.Path(file).stat().st_size)

#####

def check_dir(dir, text="checked directory"):
    if os.path.exists(dir) is False:
        return(f"Path ({dir}) for {text} does not exist")

    if os.path.isdir(dir) is False:
        return(text+" directory ("+dir+") does not exist")

    return("")

##

def check_existing_dir_w(dir, text="checked directory"):
    err = check_dir(dir, text=text)
    if isNotBlank(err):
        return(err)
    if os.access(dir, os.W_OK) is False:
        return(text+" directory ("+dir+") unable to write to")
    return("")

###

def make_wdir(dir, text="destination directory"):
    if os.path.isdir(dir) is True:
        return(check_existing_dir_w(dir, text))
    
    try:
        os.mkdir(dir, 0o755)
    except OSError as e:
        x = str(e)
        return(f"Problem creating {text} directory {dir}: {x}")

    return("")

###

def make_wdir_error(dest_dir):
    err = make_wdir(dest_dir)
    if isNotBlank(err):
        error_exit(err)

###

def get_dirlist(dir, text="checked directory"):
    err = check_dir(dir, text)
    if isNotBlank(err):
        return(err, [])
    
    listing = os.listdir(dir)
    return("", listing)

##########

def get_timeUTC():
    return(datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))

#####

def get_runid():
    if 'webui_runid' not in st.session_state:
        st.session_state['webui_runid'] = get_timeUTC()

    runid = st.session_state['webui_runid']
    return runid

#####


def get_run_file(run_file):
    err = check_file_r(run_file)
    if isNotBlank(err):
        error_exit(err)
    with open(run_file, 'r') as f:
        run_json = json.load(f)
    return (run_json)

#####

def error_exit(txt):
    print("[ERROR] " + txt)
    sys.exit(1)

##########
    
def directory_rmtree(dir):
    if os.path.isdir(dir) is False:
        return("")
    try:
        shutil.rmtree(dir, ignore_errors=True)
    except OSError as e:
        x = str(e)
        return(f"Problem deleting directory {dir}: {x}")

    return("")

def get_dirname(path):
    return(os.path.dirname(path))

#####

def get_history(search_dir):
    hist = {}
    err, listing = get_dirlist(search_dir, "save location")
    if isNotBlank(err):
        st.error(f"While getting directory listing from {search_dir}: {err}, history will be incomplete")
        return hist
    for entry in listing:
        entry_dir = os.path.join(search_dir, entry)
        err = check_existing_dir_w(entry_dir)
        if isNotBlank(err):
            st.error(f"While checking {entry_dir}: {err}, history will be incomplete")
            continue
        for file in os.listdir(entry_dir):
            if fnmatch.fnmatch(file, 'run---*.json'):
                run_file = os.path.join(entry_dir, file)
                run_json = get_run_file(run_file)
                if 'prompt' in run_json:
                    prompt = run_json['prompt']
                    hist[entry] = [prompt, run_file]
                break
    return hist

#####

def show_history(hist, allow_history_deletion, last_prompt_key, last_query_key):
    hk = [x for x in hist.keys() if isNotBlank(x)]
    hk = sorted(hk, reverse=True)
    hk_opt = [hist[x][0] for x in hk]
    hk_q = {hist[x][0]: hist[x][1] for x in hk}
    prev = st.selectbox("Prompt History (most recent first)", options=hk_opt, index=0, key="history")
    if st.button("Load Selected Prompt", key="load_history"):
        st.session_state[last_prompt_key] = prev
        st.session_state[last_query_key] = hk_q[prev]
    if allow_history_deletion:
        if st.button("Delete Selected Prompt", key="delete_history"):
            if isNotBlank(prev):
                dir = os.path.dirname(hk_q[prev])
                err = directory_rmtree(dir)
                if isNotBlank(err):
                    st.error(f"While deleting {dir}: {err}")
                else:
                    if os.path.exists(dir):
                        st.error(f"Directory {dir} still exists")
                    else:
                        st.success(f"Deleted")
            else:
                st.error("Please select a prompt to delete")
