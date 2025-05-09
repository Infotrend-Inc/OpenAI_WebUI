ARG OAIWUI_BASE="python:3.12-slim-bookworm"
FROM ${OAIWUI_BASE}

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -y --fix-missing\
  && apt-get install -y --no-install-recommends \
    apt-utils locales wget curl ca-certificates build-essential \
  && apt-get clean

# UTF-8
RUN localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG=en_US.utf8 \
  LC_ALL=C \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_ROOT_USER_ACTION=ignore

# Setup pip
RUN wget -q -O /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py \
  && python3 /tmp/get-pip.py \
  && pip3 install -U pip \
  && rm -rf /tmp/get-pip.py /root/.cache/pip

# Install uv
# https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

# Verify that the virtual environment is active and uv is installed
RUN which python3 && python3 --version
RUN which uv && uv --version

# Get the source code
RUN mkdir /app /app/.streamlit /app/assets /iti
COPY pyproject.toml OAIWUI_WebUI.py common_functions.py common_functions_WebUI.py OAIWUI_Images.py OAIWUI_Images_WebUI.py OAIWUI_GPT.py OAIWUI_GPT_WebUI.py ollama_helper.py models.json /app/
COPY assets/Infotrend_Logo.png /app/assets/

# Sync the project into a new environment
WORKDIR /app
RUN uv tool install --with-requirements pyproject.toml streamlit

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["uvx", "streamlit", "run", "OAIWUI_WebUI.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--browser.gatherUsageStats=False", "--logger.level=info"]
