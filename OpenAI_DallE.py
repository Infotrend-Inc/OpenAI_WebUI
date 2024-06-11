import openai
from openai import OpenAI

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
    # using list from venv/lib/python3.11/site-packages/openai/_exceptions.py
    except openai.APIConnectionError as e:
        return(f"OpenAI API request failed to connect: {e}", "")
    except openai.AuthenticationError as e:
        return(f"OpenAI API request was not authorized: {e}", "")
    except openai.RateLimitError as e:
        return(f"OpenAI API request exceeded rate limit: {e}", "")
    except openai.APIError as e:
        return(f"OpenAI API returned an API Error: {e}", "")
    except openai.OpenAIError as e:
        return(f"OpenAI API request failed: {e}", "")

    return "", response


##########
class OAI_DallE:
    def __init__(self, apikey, base_save_location, username):
        print("---------- [INFO] In OAI_DallE __init__ ----------")

        self.last_dalle_query = 'last_dalle_query'

        self.apikey = apikey
        self.save_location = os.path.join(base_save_location, username)
        err = cf.make_wdir_recursive(self.save_location)
        if cf.isNotBlank(err):
            cf.error_exit(err) # nothing else to do here
        self.models = {}
        self.models_status = {}
        self.model_help = ""
        self.per_model_help = {}

        self.dalle_modes = {
            "Image": "The image generations endpoint allows you to create an original image given a text prompt. Generated images and maximum number of requested images depends on the model selected. Smaller sizes are faster to generate."
        }
        self.dalle_help = ""
        for key in self.dalle_modes:
            self.dalle_help += key + ":\n"
            self.dalle_help += self.dalle_modes[key] + "\n"


#####
    def set_parameters(self, models_list, av_models_list):
        models = {}
        models_status = {}
        model_help = ""

        warning = ""

        s_models_list = models_list.replace(",", " ").split()
        known_models = list(av_models_list.keys())
        for t_model in s_models_list:
            model = t_model.strip()
            if model in av_models_list:
                if av_models_list[model]["status"] == "deprecated":
                    warning += f"Model [{model}] is deprecated (" + av_models_list[model]['status_details'] + "), discarding it"
                else:
                    models[model] = dict(av_models_list[model])
                    if cf.isNotBlank(models[model]["status_details"]):
                        models_status[model] = av_models_list[model]["status"] + " (" + av_models_list[model]["status_details"] + ")"
            else:
                return f"Unknown model: [{model}] | Known models: {known_models}", warning

        model_help = ""
        for key in models:
            per_model_help = f"{key} (" + av_models_list[key]["status"] + "):\n"
            per_model_help += av_models_list[key]["label"] + "\n"
            per_model_help += "image_size: " + str(av_models_list[key]["image_size"])
            if cf.isNotBlank(models[key]["status_details"]):
                per_model_help += " NOTE: " + models[key]["status_details"]
            self.per_model_help[key] = per_model_help
            model_help += f"{per_model_help}\n\n"

        active_models = [x for x in av_models_list if av_models_list[x]["status"] == "active"]
        active_models_txt = ",".join(active_models)

        if len(models) == 0:
            return f"No models retained, unable to continue. Active models: {active_models_txt}", warning

        model_help += "For a list of available supported models, see https://github.com/Infotrend-Inc/OpenAI_WebUI\n\n"
        model_help += f"List of active models supported by this release: {active_models_txt}\n\n"

        self.models = models
        self.models_status = models_status
        self.model_help = model_help

        return "", warning

#####
    def get_dest_dir(self):
        return os.path.join(self.save_location, "dalle", cf.get_timeUTC())

    def get_models(self):
        return self.models

    def get_models_status(self):
        return self.models_status
    
    def get_model_help(self):
        return self.model_help

    def get_per_model_help(self):
        return self.per_model_help

    def get_dalle_modes(self):
        return self.dalle_modes

    def get_save_location(self):
        return self.save_location

#####
    def dalle_it(self, model, prompt, img_size, img_count, dest_dir, st_placeholder = None, **kwargs):
        err = cf.make_wdir_recursive(dest_dir)
        err = cf.check_existing_dir_w(dest_dir)
        if cf.isNotBlank(err):
            return f"While checking {dest_dir}: {err}", ""

        err, response = dalle_call(self.apikey, model, prompt, img_size, img_count, **kwargs)
        if cf.isNotBlank(err):
            return err, ""

        all_images = []
        for i in range(img_count):
            image_name = f"{dest_dir}/{i + 1}.png"
            image_url = response.data[i].url
            if st_placeholder:
                st_placeholder.info(f"Downloading result {i + 1} as {image_name}")
            img_data = requests.get(image_url).content
            with open(image_name, 'wb') as handler:
                handler.write(img_data)
            all_images.append(image_name)
        if st_placeholder:
            st_placeholder.empty()

        run_file = f"{dest_dir}/run.json"
        run_json = {
            "prompt": prompt,
            "images": all_images,
        }
        with open(run_file, 'w') as f:
            json.dump(run_json, f, indent=4)

        return "", run_file

#####
    def get_history(self):
        search_dir = os.path.join(self.save_location, "dalle")
        return cf.get_history(search_dir)
