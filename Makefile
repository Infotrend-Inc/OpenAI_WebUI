SHELL := /bin/bash
.PHONY: all

# Base python image base on Debian
OAIWUI_BASE="ubuntu:24.04"

# Version infomation and container name
OAIWUI_VERSION="0.9.11"

OAIWUI_CONTAINER_NAME="openai_webui"

# Default build tag
OAIWUI_BUILD="${OAIWUI_CONTAINER_NAME}:${OAIWUI_VERSION}"
OAIWUI_BUILD_LATEST="${OAIWUI_CONTAINER_NAME}:latest"

OAIWUI_BUILDX="oaiwui"

all:
	@echo "** Available Docker images to be built (make targets):"
	@echo "build:          will build the ${OAIWUI_BUILD} image and tag it as latest as well"
	@echo "delete:         will delete the main latest image"
	@echo "buildx_rm:      will delete the buildx builder"

buildx_prep:
	@docker buildx ls | grep -q ${OAIWUI_BUILDX} && echo \"builder already exists -- to delete it, use: docker buildx rm ${OAIWUI_BUILDX}\" || docker buildx create --name ${OAIWUI_BUILDX} --driver-opt env.BUILDKIT_STEP_LOG_MAX_SIZE=256000000
	@docker buildx use ${OAIWUI_BUILDX} || exit 1


build:
	@make buildx_prep
	@BUILDX_EXPERIMENTAL=1 docker buildx debug --on=error build --progress plain --build-arg OAIWUI_BASE=${OAIWUI_BASE} -t ${OAIWUI_BUILD} --load -f Dockerfile .
	@docker tag ${OAIWUI_BUILD} ${OAIWUI_BUILD_LATEST}

delete:
	@docker rmi ${OAIWUI_BUILD_LATEST}
	@docker rmi ${OAIWUI_BUILD}

buildx_rm:
	@docker buildx ls | grep -q ${OAIWUI_BUILDX} || echo "builder does not exist"
	@echo "** About to delete buildx: ${OAIWUI_BUILDX}"
	@echo "Press Ctl+c within 5 seconds to cancel"
	@for i in 5 4 3 2 1; do echo -n "$$i "; sleep 1; done; echo ""
	@docker buildx rm ${OAIWUI_BUILDX}
##


docker_push:
	@echo "Creating docker hub tags -- Press Ctl+c within 5 seconds to cancel -- will only work for maintainers"
	@for i in 5 4 3 2 1; do echo -n "$$i "; sleep 1; done; echo ""
	@make build
	@docker tag ${OAIWUI_BUILD} infotrend/${OAIWUI_BUILD}
	@docker tag ${OAIWUI_BUILD_LATEST} infotrend/${OAIWUI_BUILD_LATEST}
	@echo "hub.docker.com upload -- Press Ctl+c within 5 seconds to cancel -- will only work for maintainers"
	@for i in 5 4 3 2 1; do echo -n "$$i "; sleep 1; done; echo ""
	@docker push infotrend/${OAIWUI_BUILD}
	@docker push infotrend/${OAIWUI_BUILD_LATEST}