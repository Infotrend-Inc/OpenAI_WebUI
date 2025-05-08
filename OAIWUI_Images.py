import openai
from openai import OpenAI

import json

import requests

import os.path
import pathlib
import base64

import common_functions as cf

from datetime import datetime


######
# https://github.com/openai/openai-openapi/blob/master/openapi.yaml
def images_call(apikey, model, prompt, img_size, img_count, resp_file:str='', **kwargs):
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

    response_dict = {}
    # Convert response to dict using model_dump() for Pydantic models
    try:
        response_dict = response.model_dump()
    except AttributeError:
        # Fallback for objects that don't support model_dump
        response_dict = vars(response)

    if cf.isNotBlank(resp_file):
        with open(resp_file, 'w') as f:
            json.dump(response_dict, f, indent=4)

    return "", response


##########
class OAIWUI_Images:
    def __init__(self, base_save_location, username):
        cf.logit("---------- In OAIWUI_Images __init__ ----------", "debug")

        self.last_images_query = 'last_images_query'

        self.apikeys = {}
        self.save_location = os.path.join(base_save_location, username)
        err = cf.make_wdir_recursive(self.save_location)
        if cf.isNotBlank(err):
            cf.error_exit(err) # nothing else to do here
        self.models = {}
        self.models_status = {}
        self.model_help = ""
        self.per_model_help = {}

        self.images_modes = {
            "Image": "The image generations endpoint allows you to create an original image given a text prompt. Generated images and maximum number of requested images depends on the model selected. Smaller sizes are faster to generate."
        }
        self.images_help = ""
        for key in self.images_modes:
            self.images_help += key + ":\n"
            self.images_help += self.images_modes[key] + "\n"

        self.per_model_provider = {}
        self.models_warning = {}
        self.known_models = {}


#####
    def check_apikeys(self, model, meta):
        if 'provider' in meta:
            provider = meta["provider"]
        else:
            return "Missing provider"

        if provider in self.apikeys:
            return "" # no need to continue, we have it

        warn, apikey = cf.check_apikeys(provider, meta)
        if cf.isNotBlank(warn):
            return warn

        self.apikeys[provider] = apikey
        return ""

#####
    def set_parameters(self, models_list, av_models_list):
        models = {}
        models_status = {}
        model_help = ""

        warning = ""

        t_models_list = models_list.replace(",", " ").split()
        known_models = list(av_models_list.keys())
        for t_model in t_models_list:
            model = t_model.strip()
            if model in av_models_list:
                if "meta" in av_models_list[model]:
                    err = self.check_apikeys(model, av_models_list[model]["meta"])
                    if cf.isNotBlank(err):
                        warning += f"Discarding Model {model}: {err}. "
                        self.models_warning[model] = f"Discarding: {err}"
                        continue
                    if 'provider' in av_models_list[model]["meta"]:
                        self.per_model_provider[model] = av_models_list[model]["meta"]["provider"]
                    else:
                        warning += f"Discarding Model {model}: Missing the provider information. "
                        self.models_warning[model] = f"Discarding: Missing the provider information"
                        continue
                else:
                    warning += f"Discarding Model {model}: Missing the meta information. "
                    self.models_warning[model] = f"Discarding: Missing the meta information"
                    continue

                if av_models_list[model]["status"] == "deprecated":
                    warning += f"Model [{model}] is deprecated (" + av_models_list[model]['status_details'] + "), discarding it"
                    self.models_warning[model] = f"deprecated (" + av_models_list[model]['status_details'] + ")"
                else:
                    models[model] = dict(av_models_list[model])
                    if cf.isNotBlank(models[model]["status_details"]):
                        models_status[model] = av_models_list[model]["status"] + " (" + av_models_list[model]["status_details"] + ")"
            else:
                warning += f"Unknown model: [{model}] | Known models: {known_models}"
                self.models_warning[model] = f"Unknown model"

        self.known_models = list(av_models_list.keys())

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
            return f"No models kept, unable to continue. Active models: {active_models_txt}", warning

        model_help += "For a list of available supported models, see https://github.com/Infotrend-Inc/OpenAI_WebUI/models.md\n\n"
        model_help += f"List of active models supported by this release: {active_models_txt}\n\n"

        self.models = models
        self.models_status = models_status
        self.model_help = model_help

        return "", warning

#####
    def get_dest_dir(self):
        return os.path.join(self.save_location, "images", cf.get_timeUTC())

    def get_models(self):
        return self.models

    def get_models_status(self):
        return self.models_status
    
    def get_model_help(self):
        return self.model_help

    def get_per_model_help(self):
        return self.per_model_help

    def get_images_modes(self):
        return self.images_modes

    def get_save_location(self):
        return self.save_location

    def get_models_warning(self):
        return self.models_warning

    def get_known_models(self):
        return self.known_models

#####
    def images_it(self, model, prompt, img_size, img_count, dest_dir, **kwargs):
        err = cf.make_wdir_recursive(dest_dir)
        err = cf.check_existing_dir_w(dest_dir)
        if cf.isNotBlank(err):
            return f"While checking {dest_dir}: {err}", ""
        resp_file = f"{dest_dir}/resp.json"

        warn = ""
        err, response = images_call(self.apikeys[self.per_model_provider[model]], model, prompt, img_size, img_count, resp_file, **kwargs)
        if cf.isNotBlank(err):
            return err, warn, ""

        all_images = []
        for i in range(img_count):
            image_name = f"{dest_dir}/{i + 1}.png"

            cf.logit(f"Downloading result {i + 1} as {image_name}", "debug")
            image_url = response.data[i].url
            image_b64 = response.data[i].b64_json
            img_bytes = None

            if image_url is not None:
                img_bytes = requests.get(image_url).content
            elif image_b64 is not None:
                img_bytes = base64.b64decode(image_b64)

            if img_bytes is not None:
                with open(image_name, 'wb') as handler:
                    handler.write(img_bytes)
                all_images.append(image_name)
            else:
                warn += f"Unable to download image {i + 1}\n"
                cf.logit(f"Unable to download image", "warning")

        if len(all_images) == 0:
            return "No images generated", warn, ""

        run_file = f"{dest_dir}/run.json"
        run_json = {
            "prompt": prompt,
            "images": all_images,
        }
        with open(run_file, 'w') as f:
            json.dump(run_json, f, indent=4)

        return "", warn, run_file

#####
    def get_history(self):
        search_dir = os.path.join(self.save_location, "images")
        return cf.get_history(search_dir)
