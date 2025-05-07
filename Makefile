SHELL := /bin/bash
.PHONY: all

# Decide which "no-cache" policy you want for your builds
#OAIWUI_NOCACHE="--no-cache"
OAIWUI_NOCACHE=

# docker/podman selection
# does not matter for unraid builds
# when using docker_push, docker must be used
DOCKER_CMD=docker
#DOCKER_CMD=podman

# Base python image base on Debian
OAIWUI_BASE="python:3.12-slim-bookworm"

# Version infomation and container name
OAIWUI_VERSION="0.9.11"

OAIWUI_CONTAINER_NAME="openai_webui"

# Default build tag
OAIWUI_BUILD="${OAIWUI_CONTAINER_NAME}:${OAIWUI_VERSION}"
OAIWUI_BUILD_LATEST="${OAIWUI_CONTAINER_NAME}:latest"

# Unraid build tag
OAIWUI_UNRAID_BUILD="${OAIWUI_CONTAINER_NAME}-unraid:${OAIWUI_VERSION}"
OAIWUI_UNRAID_BUILD_LATEST="${OAIWUI_CONTAINER_NAME}-unraid:latest"

all:
	@echo "** Available Docker images to be built (make targets):"
	@echo "build:          will build both latest and unraid images"
	@echo "  build_main:   will build the ${OAIWUI_BUILD} image and tag it as latest as well"
	@echo "  build_unraid: will build the ${OAIWUI_UNRAID_BUILD} image and tag it as latest as well"
	@echo ""
	@echo "delete_images:   will delete the main and unraid images"
	@echo "  delete_unraid: will delete the unraid images (has to be done before you can delete the other)"
	@echo "  delete_main:   will delete the main latest images"

build_main:
	@${DOCKER_CMD} build --build-arg OAIWUI_BASE=${OAIWUI_BASE} ${OAIWUI_NOCACHE} -t ${OAIWUI_BUILD} -f Dockerfile .
	@${DOCKER_CMD} tag ${OAIWUI_BUILD} ${OAIWUI_BUILD_LATEST}

build_unraid:
	@docker build --build-arg OAIWUI_BUILD=${OAIWUI_BUILD} ${OAIWUI_NOCACHE} -t ${OAIWUI_UNRAID_BUILD} -f unraid/Dockerfile .
	@docker tag ${OAIWUI_UNRAID_BUILD} ${OAIWUI_UNRAID_BUILD_LATEST}

build:
	@make build_main
	@make build_unraid

delete_unraid:
	@docker rmi ${OAIWUI_UNRAID_BUILD_LATEST}
	@docker rmi ${OAIWUI_UNRAID_BUILD}

delete_main:
	@${DOCKER_CMD} rmi ${OAIWUI_BUILD_LATEST}
	@${DOCKER_CMD} rmi ${OAIWUI_BUILD}

delete_images:
	@make delete_unraid
	@make delete_main

##

build_docker_amd64:
	@docker buildx build --platform linux/amd64 --build-arg OAIWUI_BASE=${OAIWUI_BASE} ${OAIWUI_NOCACHE} -t ${OAIWUI_BUILD} -f Dockerfile .
	@docker tag ${OAIWUI_BUILD} ${OAIWUI_BUILD_LATEST}
	@docker buildx build --platform linux/amd64 --build-arg OAIWUI_BUILD=${OAIWUI_BUILD} ${OAIWUI_NOCACHE} -t ${OAIWUI_UNRAID_BUILD} -f unraid/Dockerfile .
	@docker tag ${OAIWUI_UNRAID_BUILD} ${OAIWUI_UNRAID_BUILD_LATEST}


docker_push:
	@echo "Creating docker hub tags -- Press Ctl+c within 5 seconds to cancel -- will only work for maintainers"
	@for i in 5 4 3 2 1; do echo -n "$$i "; sleep 1; done; echo ""
	@make build_main
	@docker tag ${OAIWUI_BUILD} infotrend/${OAIWUI_BUILD}
	@docker tag ${OAIWUI_BUILD_LATEST} infotrend/${OAIWUI_BUILD_LATEST}
	@make build_unraid
	@docker tag ${OAIWUI_UNRAID_BUILD} infotrend/${OAIWUI_UNRAID_BUILD}
	@docker tag ${OAIWUI_UNRAID_BUILD_LATEST} infotrend/${OAIWUI_UNRAID_BUILD_LATEST}
	@echo "hub.docker.com upload -- Press Ctl+c within 5 seconds to cancel -- will only work for maintainers"
	@for i in 5 4 3 2 1; do echo -n "$$i "; sleep 1; done; echo ""
	@docker push infotrend/${OAIWUI_BUILD}
	@docker push infotrend/${OAIWUI_BUILD_LATEST}
	@docker push infotrend/${OAIWUI_UNRAID_BUILD}
	@docker push infotrend/${OAIWUI_UNRAID_BUILD_LATEST}