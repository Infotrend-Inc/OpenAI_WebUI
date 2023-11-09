import os
import os.path
import pathlib
import sys

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
    return(datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"))

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