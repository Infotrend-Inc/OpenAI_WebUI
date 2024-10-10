ARG OAI_BASE="python:3.12-slim-bookworm"
FROM ${OAI_BASE}

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
  POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry'

# Setup pip
RUN wget -q -O /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py \
  && python3 /tmp/get-pip.py \
  && pip3 install -U pip \
  && rm /tmp/get-pip.py

RUN mkdir /app
WORKDIR /app
COPY pyproject.toml /app/
RUN pip3 --trusted-host pypi.org --trusted-host files.pythonhosted.org install poetry \
  && poetry install --compile \
  && rm -rf /root/.cache/pip /var/cache/pypoetry

RUN mkdir /app/.streamlit /app/assets /iti
RUN streamlit cache clear
COPY OpenAI_WebUI.py common_functions.py common_functions_WUI.py OpenAI_DallE.py OpenAI_DallE_WUI.py OpenAI_GPT.py OpenAI_GPT_WUI.py models.json /app/
COPY assets/Infotrend_Logo.png /app/assets/

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "OpenAI_WebUI.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--browser.gatherUsageStats=False", "--logger.level=debug"]
