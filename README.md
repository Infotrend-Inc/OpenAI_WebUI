# OpenAI WebUI

<!-- vscode-markdown-toc -->
* 1. [Description](#Description)
	* 1.1. [.env](#env)
	* 1.2. [savedir](#savedir)
* 2. [Setup](#Setup)
	* 2.1. [Python virtualenv](#Pythonvirtualenv)
	* 2.2. [Docker/Podman](#DockerPodman)
	* 2.3. [Unraid](#Unraid)
* 3. [Misc](#Misc)
	* 3.1. [Warning](#Warning)
	* 3.2. [Version information](#Versioninformation)
	* 3.3. [Acknowledgements](#Acknowledgements)

<!-- vscode-markdown-toc-config
	numbering=true
	autoSave=true
	/vscode-markdown-toc-config -->
<!-- /vscode-markdown-toc -->

WebUI ([streamlit](https://streamlit.io/)-based) to ChatGPT and Dall-E's API (requires an OpenAI API key).

The tool's purpose is to enable a company to install a self-hosted version of a WebUI to access the capabilities of OpenAI's ChatGPT and DallE and share access to the tool's capabilities while consolidating billing through an OpenAI API key.

A pre-built container is available from our Docker account at https://hub.docker.com/r/infotrend/openai_webui

Note: this tool was initially developed in February 2023 and released to help end-users.

##  1. <a name='Description'></a>Description

The tool provides a WebUI to ChatGPT and Dall-E (that later one can be disabled).

The tool **requires** the use of an OpenAI API key to work.
Check at https://platform.openai.com/account/api-keys to find yours.

Depending on your deployment solution (*python virtualenv*, *docker image*, or *unraid*), the deployment might differ slightly.

Once started, the WebUI will prompt the end user with a `username`. 
This username is here to make finding past conversations/images easier if you seek those; no authentication is associated with it.

The GPT WebUI allows the user to select the `model` to use, the `role` of the assistant, the `max tokens`, and the `temperature` of the response. Each parameter has a help text to provide details within the UI.

The Dall-E WebUI allows the user to specify the `image size` and `number of images` to generate. 

###  1.1. <a name='env'></a>.env

The `.env.example` file contains the parameters needed to pass to the running tool:
- `OPENAI_API_KEY` as obtained from https://platform.openai.com/account/api-keys
- `OAIWUI_SAVEDIR`, the location to save content (make sure the directory exists)
- `OAIWUI_GPT_ONLY`, to request only to show the GPT tab otherwise, shows both GPT and DallE (authorized value: `True` or `False`)
- `OAIWUI_MODELS` is the list of GPT models your API key is authorized to use. See https://platform.openai.com/docs/api-reference/making-requests for more information.

Those values can be passed by making a `.env` file containing the expected values or using environment variables.

The `.env` file is not copied into the `docker` or `unraid` setup. Environment variables should be used in this case. 

###  1.2. <a name='savedir'></a>savedir

The `OAIWUI_SAVEDIR` variable specifies the location where persistent files will be created from run to run.

Its structure is: `savedir`/`version`/`username`/`mode`/`UTCtime`/`<CONTENT>`, with:
- `username` being the self-specified user name prompted when starting the WebUI
- `version` the tool's version, making it easier to debug
- `mode` on of `gpt` or `dalle`
- the `UTCtime`, a `YYYYY-MM-DD T HH:MM:SS.microseconds Z` UTC-time of the request (the directory's content will be time ordered)
- `<CONTENT>` is often a `json` file containing the details of the run for `gpt`, but also the different `png` images generated for `dalle`

We do not check the directories for size. It is left to the end user to clean up space if required.

##  2. <a name='Setup'></a>Setup

###  2.1. <a name='Pythonvirtualenv'></a>Python virtualenv

This mode is for use if you have `python3` installed and want to test the tool.

1. Create and activate your virtual environment

    ```bash
    $ python3 -m venv venv
    $ source venv/bin/activate
    ```

1. Install the requirements within our activated virtual environment

   ```bash
   $ pip install -U pip
   $ pip3 install -r requirements.txt
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

###  2.2. <a name='DockerPodman'></a>Docker/Podman

The container build is an excellent way to test in an isolated, easily redeployed environment.

This setup prefers the use of environment variable, using `docker run ... -e VAR=val`

1. Build the container

    ```bash
    $ make build_main
    ```

1. Run the built container, here specifying your `OAIWUI_SAVEDIR` to be `/iti`, which will be mounted from the current working directory's `savedir` and mounted to `/iti` within the container:

    ```bash
    $ docker run --rm -it -p 8501:8501 -v `pwd`/savedir:/iti -e OPENAI_API_KEY="Your_OpenAI_API_Key" -e OAIWUI_SAVEDIR=/iti -e OAIWUI_GPT_ONLY=False -e OAIWUI_GPT_MODELS="gpt-3.5-turbo,gpt-3.5-turbo-16k,gpt-4" -e OAIWUI_DALLE_MODELS="dall-e-2,dall-e-3" openai_webui:latest
    ```

You can have the `Makefile` delete locally built containers:

```
$ make delete_main
```

###  2.3. <a name='Unraid'></a>Unraid

For [Unraid](https://unraid.net/) users, a special build mode is available to get a container using unraid's preferred `uid`/`gid`. 

##  3. <a name='Misc'></a>Misc

###  3.1. <a name='Warning'></a>Warning

Sometimes, you will run into an error when starting the tool. Clear the `streamlit` cache (right side menu) or deleting cookies should solve this.

###  3.2. <a name='Versioninformation'></a>Version information

- Nov 8th, 2023: incorporating modifications brought by the latest OpenAI Python package (tested against 1.2.0)
- Oct 2023: Preparation for public release
- Feb 2023: Initial version

###  3.3. <a name='Acknowledgements'></a>Acknowledgements

This project includes contributions from [Yan Ding](https://www.linkedin.com/in/yan-ding-01a429108/) and [Muhammed Virk](https://www.linkedin.com/in/mhmmdvirk/) in March 2023.

