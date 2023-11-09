ARG OAI_BUILD="openai_webui:latest"
FROM ${OAI_BUILD}

USER root
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y --no-install-recommends sudo
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers && \
    (addgroup --group --gid 100 unraid || true) && \
    adduser --force-badname --disabled-password --gecos '' --uid 99 --gid 100 --shell /bin/bash unraid && \
    adduser unraid sudo 

USER unraid
RUN sudo chown -R unraid /home/unraid /iti

# Similar last lines to original Dockerfile
EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "/app/OpenAI_WebUI.py", "--server.port=8501", "--server.address=0.0.0.0"]