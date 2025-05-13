ARG OAIWUI_BASE="ubuntu:24.04"
FROM ${OAIWUI_BASE}

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -y --fix-missing\
  && apt-get upgrade -y \
  && apt-get install -y --no-install-recommends \
    apt-utils locales wget curl ca-certificates build-essential sudo python3 python3-dev \
  && apt-get clean

# UTF-8
RUN localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG=en_US.utf8 \
  LC_ALL=C \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_ROOT_USER_ACTION=ignore

# Setup pip
RUN mv /usr/lib/python3.12/EXTERNALLY-MANAGED /usr/lib/python3.12/EXTERNALLY-MANAGED.old \
  && wget -q -O /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py \
  && python3 /tmp/get-pip.py \
  && pip3 install -U pip \
  && rm -rf /tmp/get-pip.py /root/.cache/pip

# Every sudo group user does not need a password
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Create a new group for the oaiwui user and the oaiwuitoo user
RUN groupadd -g 1024 oaiwui \
  && groupadd -g 1025 oaiwuitoo

# The oaiwui user will have UID 1024, 
# be part of the oaiwui and users groups and be sudo capable (passwordless) 
RUN useradd -u 1024 -d /home/oaiwui -g oaiwui -s /bin/bash -m oaiwui \
    && usermod -G users oaiwui \
    && usermod -aG sudo oaiwui
# The oaiwuitoo user will have UID 1025 ...
RUN useradd -u 1025 -d /home/oaiwuitoo -g oaiwuitoo -s /bin/bash -m oaiwuitoo \
    && usermod -G users oaiwuitoo \
    && usermod -aG sudo oaiwuitoo

# Setup uv as oaiwuitoo
USER oaiwuitoo

# Install uv
# https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
RUN wget https://astral.sh/uv/install.sh -O /tmp/uv-installer.sh \
  && sh /tmp/uv-installer.sh \
  && rm /tmp/uv-installer.sh
ENV PATH="/home/oaiwuitoo/.local/bin/:$PATH"

# Verify that python3 and uv are installed
RUN which python3 && python3 --version
RUN which uv && uv --version

# Get the source code (making sure the directories are owned by oaiwuitoo and the users group shared by oaiwui and oaiwuitoo)
RUN sudo mkdir /app /app/.streamlit /app/assets /iti \
    && sudo chown -R oaiwuitoo:users /app /iti

COPY pyproject.toml OAIWUI_WebUI.py common_functions.py common_functions_WebUI.py OAIWUI_Images.py OAIWUI_Images_WebUI.py OAIWUI_GPT.py OAIWUI_GPT_WebUI.py ollama_helper.py models.json /app/
COPY assets/Infotrend_Logo.png /app/assets/

# Sync the project into a new environment
WORKDIR /app
RUN uv sync \
  && uv clean cache
# Check that the venv is created with the expected tools
RUN test -d /app/.venv \
  && test -x /app/.venv/bin/python3 \
  && test -x /app/.venv/bin/streamlit

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Final copies (as root, done at the end to avoid rebuilding previous steps)
USER root

RUN chown -R oaiwui:users /app /iti
COPY --chmod=755 entrypoint.sh /entrypoint.sh
COPY --chmod=644 config.sh /oaiwui_config.sh

# Run as oaiwuitoo
USER oaiwuitoo

# The entrypoint will enable us to switch to the oaiwui user and run the application
ENTRYPOINT ["/entrypoint.sh"]
