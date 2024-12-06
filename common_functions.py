import os
import os.path
import pathlib
import sys
import shutil
import fnmatch
import stat

import json

from datetime import datetime

iti_version="0.9.9"

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
        return(f"{text} ({file}) does not exist")
    if not os.path.isfile(file):
        return(f"{text} ({file}) is not a file")
    return("")

##

def check_file_r(file, text="checked file"):
    err = check_file(file, text)
    if isNotBlank(err):
        return(err)
    permissions = stat.S_IMODE(os.lstat(file).st_mode)
    if not (permissions & stat.S_IRUSR):
        return(f"{text} ({file}) can not be read")
    return("")

##

def check_existing_file_w(file, text="checked file"):
    err = check_file(file, text)
    if isNotBlank(err):
        return err
    permissions = stat.S_IMODE(os.lstat(file).st_mode)
    if not (permissions & stat.S_IWUSR):
        return f"{text} ({file}) unable to write"
        
    return ""    

##

def check_file_w(file, text="checked file"):
    err = check_file(file, text)
    if isBlank(err):
        # The file already exist, lets check if we can write to it
        err = check_existing_file_w(file, text)
        if isNotBlank(err):
            # The file is not writable
            return f"{text} ({file}) file exists but we are unable to write"
        return "" # the file exists and is writable, we are done here
    
    # if the file does not exist, we will try to create it
    file_obj = open(file, "a") # open in append mode to create the file
    file_obj.close()
    # we created a file that should be writable, let's check again
    return check_existing_file_w(file, text)

##

def check_file_size(file, text="checked file"):
    err = check_file_r(file, text)
    if isNotBlank(err):
        return(err, 0)
    return("", pathlib.Path(file).stat().st_size)

#####

def check_dir(dir, text="checked directory"):
    if os.path.exists(dir) is False:
        return f"Path ({dir}) for {text} does not exist"

    if os.path.isdir(dir) is False:
        return f"{text} directory ({dir}) does not exist"

    return("")

##

def check_existing_dir_w(dir, text="checked"):
    err = check_dir(dir, text=text)
    if isNotBlank(err):
        return err
    permissions = stat.S_IMODE(os.lstat(dir).st_mode)
    if not (permissions & stat.S_IWUSR):
        return f"{text} directory ({dir}) unable to write to"
    return ""

###

def make_wdir(dir, text="destination"):
    if os.path.isdir(dir) is True:
        return check_existing_dir_w(dir, text)

    # the directory does not exist, we will try to create it
    os.mkdir(dir, 0o755)
    # and test if we were successful
    return check_existing_dir_w(dir, text)

###

def make_wdir_recursive(dir, text="destination"):
    if os.path.isdir(dir) is True:
        return check_existing_dir_w(dir, text)

    # the directories does not exist, we will try to create them
    pathlib.Path(dir).mkdir(parents=True, exist_ok=True)
    # and test if we were successful
    return check_existing_dir_w(dir, text)


def make_wdir_error(dest_dir):
    err = make_wdir(dest_dir)
    if isNotBlank(err):
        error_exit(err)

###

def get_dirlist(dir, text="checked directory"):
    err = check_dir(dir, text)
    if isNotBlank(err):
        return (err, [])

    listing = os.listdir(dir)
    return ("", listing)

##########

def get_timeUTC():
    return(datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))

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
        return f"While getting directory listing from {search_dir}: {err}, history will be incomplete", hist
    for entry in listing:
        entry_dir = os.path.join(search_dir, entry)
        if os.path.isdir(entry_dir) is True:
            err = check_existing_dir_w(entry_dir)
            if isNotBlank(err):
                return f"While checking {entry_dir}: {err}, history will be incomplete", hist
            for file in os.listdir(entry_dir):
                if fnmatch.fnmatch(file, 'run.json'):
                    run_file = os.path.join(entry_dir, file)
                    run_json = get_run_file(run_file)
                    if 'prompt' in run_json:
                        prompt = run_json['prompt']
                        hist[entry] = [prompt, run_file]
                    break
    return "", hist

#####

def read_json(file, txt=''):
    err = check_file_r(file)
    if err != "":
        error_exit(f"Problem with input {txt} Json file ({file}): {err}")

    with open(file) as simple_file:
        file_contents = simple_file.read()
        parsed_json = json.loads(file_contents)
        return parsed_json
