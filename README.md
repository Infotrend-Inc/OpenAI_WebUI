<h1>OpenAI WebUI</h1>

Latest version: 0.9.7 (20240718)

- [1. Description](#1-description)
  - [1.1. Supported models](#11-supported-models)
  - [1.2. .env](#12-env)
  - [1.3. savedir](#13-savedir)
  - [1.4. password protecting the WebUI](#14-password-protecting-the-webui)
- [2. Setup](#2-setup)
  - [2.1. Python virtualenv](#21-python-virtualenv)
  - [2.2. Docker/Podman](#22-dockerpodman)
  - [2.3. Docker compose](#23-docker-compose)
  - [2.4. Unraid](#24-unraid)
- [3. Misc](#3-misc)
  - [3.1. Notes](#31-notes)
  - [3.2. Version information/Changelog](#32-version-informationchangelog)
  - [3.3. Acknowledgments](#33-acknowledgments)

WebUI ([streamlit](https://streamlit.io/)-based) to ChatGPT and Dall-E's API (requires an OpenAI API key).

The tool's purpose is to enable a company to install a self-hosted version of a WebUI to access the capabilities of OpenAI's ChatGPT and DallE and share access to the tool's capabilities while consolidating billing through the [OpenAI API](https://pypi.org/project/openai/) key. Access to [models](https://platform.openai.com/docs/models/) is limited to those enabled with your API key.

Click on the links to see a screenshot of the [GPT WebUI](./assets/Screenshot-OAI_WebUI_GPT.jpg) and the [DallE WebUI](./assets/Screenshot-OAI_WebUI_DallE.jpg).

Please see https://github.com/Infotrend-Inc/OpenAI_WebUI/blob/main/.env.example for details of possible values for the environment variables. 
Unless specified, even if a feature is not used, its environment variable should be set.

A pre-built container is available from our Docker account at https://hub.docker.com/r/infotrend/openai_webui

An [Unraid](https://unraid.net/)-ready version is available directly from Unraid's `Community Applications``.

Note: this tool was initially developed in February 2023 and released to help end-users.

#  1. Description

The tool provides a WebUI to ChatGPT and Dall-E (that later one can be disabled).

The tool **requires** the use of an OpenAI API key to work.
Check at https://platform.openai.com/account/api-keys to find yours.

Depending on your deployment solution (*python virtualenv*, *docker image*, or *unraid*), the deployment might differ slightly.

Once started, the WebUI will prompt the end user with a `username`. 
This username is here to make finding past conversations/images easier if you seek those; no authentication is associated with it.

ChatGPT (Text Generation) sidebar options (see "?" mark for specific details):
- model: choose between the different ChatGPT models that are enabled.
- role (user, system, assistant): define the role of the input text for tailored responses.
- max tokens: controls the length of generated text with a maximum token setting (dependent on the model)
- temperature: adjust the "surprisingness" of the generated text.

DALL-E (Image Generation) sidebar options (see "?" for specific details):
- mode: "image" for the time being.
- model: choose between the different DallE models that are enabled.
- image Size: specify the dimensions of the images to be generated.
- number of images (model dependent): number of images to generate
- quality (model dependent): fine-tune image quality to meet your requirements.
- style  (model dependent): style of the generated images.

## 1.1. Supported models

We have added means to inform the end-user when a model is `deprecated`, `legacy` or `current`.
- `deprecated` models are not available for use anymore.
- `legacy` models will be deprecated at a specified date.
- `current` models are available.

The tool will automatically discard known (per the release) `deprecated` models and inform the end user. 
Similarly, the tool will note when a model is `legacy`.
Please update your model selection accordingly.

The [models.json](models.json) file contains the list of models supported by each release (as introduced in v0.9.3).
The following table shows the [models](https://platform.openai.com/docs/models/) listed in this file as well as the release it was added to:

| Mode | Model | Status | Capability | Notes | From |
| --- | --- | --- | --- | --- | --- |
| DallE | dalle-e-2 | active | | | 0.9.3 |
| DallE | dalle-e-3 | active | | | 0.9.3 |
| GPT | gpt-3.5-turbo | active | | | 0.9.3 |
| GPT | gpt-3.5-turbo-0125 | active | | | 0.9.3 |
| GPT | gpt-3.5-turbo-0613 | deprecated | | Deprecated on June 13, 2024 | 0.9.3 |
| GPT | gpt-3.5-turbo-1106 | active | | | 0.9.3 |
| GPT | gpt-3.5-turbo-16k | deprecated | | Deprecated on June 13, 2024 | 0.9.3 |
| GPT | gpt-3.5-turbo-16k-0613 | deprecated | |  Deprecated on June 13, 2024 | 0.9.3 |
| GPT | gpt-4 | active | | | 0.9.3 |
| GPT | gpt-4-0125-preview | active | | | 0.9.3 |
| GPT | gpt-4-0613 | active | | | 0.9.3 |
| GPT | gpt-4-1106-preview | active | | | 0.9.3 |
| GPT | gpt-4-32k | deprecated | | | 0.9.3 |
| GPT | gpt-4-32k-0613 | deprecated | | |  0.9.3 |
| GPT | gpt-4-turbo-preview | active | | | 0.9.3 |
| GPT | gpt-4-turbo | active | vision | | 0.9.5 |
| GPT | gpt-4-turbo-2024-04-09 | active | vision | | 0.9.5 |
| GPT | gpt-4o | active | vision | | 0.9.4 |
| GPT | gpt-4o-2024-05-13 | active | vision | | 0.9.4 |
| GPT | gpt-4o-mini | active | vision | | 0.9.7 |
| GPT | gpt-4o-mini-2024-07-18 | active | vision | | 0.9.7 |


Once a model is `deprecated`, using it in your models list will have it discarded from the available list with a notification. 

Similarly, if a used model is listed as `legacy`, a notification of the upcoming deprecation will be shown in the UI.

## 1.2. .env

The `.env.example` file contains the parameters needed to pass to the running tool:
- `OPENAI_API_KEY` as obtained from https://platform.openai.com/account/api-keys
- `OAIWUI_SAVEDIR`, the location to save content (make sure the directory exists)
- `OAIWUI_GPT_ONLY`, to request only to show the GPT tab otherwise, shows both GPT and DallE (authorized value: `True` or `False`)
- `OAIWUI_GPT_MODELS` is a comma-separated list of GPT model(s) your API key is authorized to use. See https://platform.openai.com/docs/api-reference/making-requests for more information.
- `OAIWUI_DALLE_MODELS` is a comma-separated list of DallE model(s) your API key is authorized to use.
- `OAIWUI_USERNAME` (optional) specifies a `username` and avoids being prompted at each re-run. The default mode is to run in multi-user settings so this is not enabled by default.
- `OAIWUI_GPT_VISION` will, for compatible models, disable their vision capabilities

Those values can be passed by making a `.env` file containing the expected values or using environment variables.

The `.env` file is not copied into the `docker` or `unraid` setup. Environment variables should be used in this case. 

## 1.3. savedir

The `OAIWUI_SAVEDIR` variable specifies the location where persistent files will be created from run to run.

Its structure is: `savedir`/`version`/`username`/`mode`/`UTCtime`/`<CONTENT>`, with:
- `username` being the self-specified user name prompted when starting the WebUI
- `version` the tool's version, making it easier to debug
- `mode` on of `gpt` or `dalle`
- the `UTCtime`, a `YYYYY-MM-DD T HH:MM:SS Z` UTC-time of the request (the directory's content will be time ordered)
- `<CONTENT>` is often a `json` file containing the details of the run for `gpt`, but also the different `png` images generated for `dalle`

We do not check the directories for size. It is left to the end user to clean up space if required.

## 1.4. password protecting the WebUI

To do this, create a `.streamlit/secrets.toml` file in the directory where the streamlit app is started (for the python virtualenv setup, this should be the directory where this `README.md` is present, while for other deployment methods, please see the corresponding [setup](#2-setup) section) and add a `password = "SET_YOUR_PASSWORD_HERE"` value to it.

When the WebUI starts, it will see of `secrets.toml` file and challenge users for the password set within.

#  2. Setup

##  2.1. Python virtualenv

This mode is for use if you have `python3` installed and want to test the tool.

1. Create and activate your virtual environment

    ```bash
    $ python3 -m venv venv
    $ source venv/bin/activate
    ```

1. Install the requirements within our activated virtual environment

   ```bash
   $ pip install -U pip
   $ pip3 install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
   ```

1. Copy the default `.env.example` file as `.env`, and manually edit the copy to add your [OpenAI API key](https://beta.openai.com/account/api-keys) and the preferred save directory (which must exist before starting the program). 
You can also configure the GPT `models` you can access with ChatGPT and disable the UI for Dall-E if preferred. 
Do not distribute that file.

   ```bash
   $ cp .env.example .env
   $ code .env
   ```

1. For developers, edit the code as you would, and when you are ready to test, start the WebUI.

    ```bash
    $ streamlit run ./OpenAI_WebUI.py --server.port=8501 --server.address=127.0.0.1 --logger.level=debug
    ```

1. You can now open your browser to http://127.0.0.1:8501 to test the WebUI.

## 2.2. Docker/Podman

The container build is an excellent way to test in an isolated, easily redeployed environment.

This setup prefers the use of environment variable, using `docker run ... -e VAR=val`

1. Build the container

    ```bash
    $ make build_main
    ```

1. Run the built container, here specifying your `OAIWUI_SAVEDIR` to be `/iti`, which will be mounted from the current working directory's `savedir` and mounted to `/iti` within the container:

    ```bash
    $ docker run --rm -it -p 8501:8501 -v `pwd`/savedir:/iti -e OPENAI_API_KEY="Your_OpenAI_API_Key" -e OAIWUI_SAVEDIR=/iti -e OAIWUI_GPT_ONLY=False -e OAIWUI_GPT_MODELS="gpt-3.5-turbo,gpt-4" -e OAIWUI_DALLE_MODELS="dall-e-2,dall-e-3" openai_webui:latest
    ```

If you want to use the password protection for the WebUI, create and populate the `.streamlit/secrets.toml` file before you start the container (see [password protecting the webui](#14-password-protecting-the-webui)) then add `-v PATH_TO/secrets.toml:/app/.streamlit/secrets.toml:ro` to your command line (adapting `PATH_TO` with the full path location of the secrets file)

You can have the `Makefile` delete locally built containers:

```
$ make delete_main
```

## 2.3. Docker compose

To run the built or downloaded container using `docker compose`, decide on the directory where you want the `compose.yaml` to be, and place the following as the content of the file:

```yaml
services:
  openai_webui:
    image: infotrend/openai_webui:latest
    container_name: openai_webui
    restart: unless-stopped
    volumes:
      - ./savedir:/iti
      # Uncomment the following and create a secrets.toml in the directory where this compose.yaml file is to password protect access to the application
      # - ./secrets.toml:/app/.streamlit/secrets.toml:ro
    ports:
      # host port:container port
      - 8501:8501
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OAIWUI_SAVEDIR=/iti
      # Adapt the following as best suits your deployment
      - OAIWUI_GPT_ONLY=False
      - OAIWUI_GPT_MODELS=gpt-4o
      - OAIWUI_GPT_VISION=True
      # Even if OAIWUI_GPT_ONLY is True, please set a model, it will be ignored
      - OAIWUI_DALLE_MODELS=dall-e-3
      # Uncomment and enter a value if you are using a single user deployment
      # - OAIWUI_USERNAME=user
```

In the directory where the `compose.yaml` is located, create a `savedir` directory (it will be mounted as `/iti` within the running container), and create a `.env` file that needs only contain the `OPENAI_API_KEY=value` entry.
If using a `secrets.toml` file with a `password=WEBUIPASSWORD` content, uncomment the entry in the `compose.yaml` file.

As configured, the container will `restart` `unless-stopped` which also means that unless the container is stopped it will automatically restart after a host reboot.

Run using `docker compose up -d`

The WebUI will be accessible on port 8501 of your host.

## 2.4. Unraid

For [Unraid](https://unraid.net/) users, a special build mode is available to get a container using unraid's preferred `uid`/`gid`, use `make build_unraid` to build it.

The pre-built container has been added to Unraid's Community Applications.

The configuration file contains many of the possible environment variables, as detailed in the [.env](#12-env) section.
Omitted from the configuration files are:
- a `Variable` named `OAIWUI_USERNAME` whose value will set a default username.
The edited XML file would add a line similar to (adapting the `username` accordingly):
    ```
    <Config Name="OAIWUI_USERNAME" Target="OAIWUI_USERNAME" Default="username" Mode="" Description="Automatically use a default user" Type="Variable" Display="always" Required="false" Mask="false">username</Config>
    ``` 
- a `Path` mapping a `secrets.toml` file to the `/app/.streamlit/secrets.toml` location within the running docker container (read-only recommended). 
Before setting this, create and populate a file with the expected value (as described in [password protecting the WebUI](#14-password-protecting-the-webui)).
For example, if your `appdata` location for the OpenAI WebUI was `/mnt/user/appdata/openai_webui` in which you placed the needed `secrets.toml` file, the expected XML addition would look similar to: 
    ```
    <Config Name="/app/.streamlit/secrets.toml" Target="/app/.streamlit/secrets.toml" Default="/mnt/user/appdata/openai_webui/secrets.toml" Mode="ro" Description="WebUI password protection -- secrets.toml file must exist with a password variable" Type="Path" Display="always" Required="false" Mask="false">/mnt/user/appdata/openai_webui/secrets.toml</Config>
    ```

# 3. Misc

##  3.1. Notes

- If you run into an error when starting the tool. Clear the `streamlit` cache (right side menu) or deleting cookies should solve this.

##  3.2. Version information/Changelog

- v0.9.7 (20240718): Added `gpt-4o-mini` and `deprecated` older `32k` models
- v0.9.6 (20240701): Added method to disable `vision` for capable models + added whole WebUI password protection using streamlit's `secrets.toml` method 
- v0.9.5 (20240611): Added support for `vision` in capable models + Added `gpt-4-turbo` models + Deprecated some models in advance of 20240613 + Updated openai python package to 1.33.0 + Decoupled UI code to allow support for different frontends.
- v0.9.4 (20240513): Added support for `gpt-4o`, updated openai python package to 1.29.0
- v0.9.3 (20240306): Simplifying integration of new models and handling/presentation of their status (active, legacy, deprecated) + Cleaner handling of max_tokens vs context window tokens + updated openai python package to 1.13.3
- v0.9.2 (20241218): Keep prompt history for a given session + allow user to review/delete past prompts + updated openai python package: 1.8.0
- v0.9.1 (20231120): Print `streamlit` errors in case of errors with environment variables + Addition of `gpt-3.5-turbo-1106` in the list of supported models (added in openai python package 1.3.0) + added optional `OAIWUI_USERNAME` environment variable
- v0.9.0 (20231108): Initial release -- incorporating modifications brought by the latest OpenAI Python package (tested against 1.2.0)
- Oct 2023: Preparation for public release
- Feb 2023: Initial version
  
## 3.3. Acknowledgments

This project includes contributions from [Yan Ding](https://www.linkedin.com/in/yan-ding-01a429108/) and [Muhammed Virk](https://www.linkedin.com/in/mhmmdvirk/) in March 2023.

