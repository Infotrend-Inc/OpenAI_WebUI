SHELL := /bin/bash
.PHONY: all

# Base python image base on Debian
OAIWUI_BASE="ubuntu:24.04"

# Version infomation and container name
OAIWUI_VERSION="0.9.12"
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
	@echo ""
	@echo "** Run the WebUI (must have uv installed):"
	@echo "uv_run:         will run the WebUI using uv"

#####
uv_run:
	uv tool run --with-requirements pyproject.toml streamlit run ./OAIWUI_WebUI.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true --server.fileWatcherType=none --browser.gatherUsageStats=False --logger.level=info

uv_run_debug:
	uv tool run --with-requirements pyproject.toml streamlit run ./OAIWUI_WebUI.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=False --logger.level=debug

#####

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

list_models:
	@python3 ./list_models.py > models.txt
	@python3 ./list_models.py --markdown > models.md

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

## Maintainers:
# - Create a new branch on GitHub that match the expected release tag, pull and checkout that branch
# - update the version number if the following files (ex: "0.9.11"):
#  common_functions.py:iti_version="0.9.11"
#  Makefile:OAIWUI_VERSION="0.9.11"
#  pyproject.toml:version = "0.9.11"
#  README.md:Latest version: 0.9.11
# - Local Test
#  % make uv_run_debug
# - Build docker image after local testing
#  % make build
# - Test in Docker then unraid
# - Upload the images to docker hub
#  % make docker_push
# - Generate the models md and txt files
#  % make list_models
# - Update the README.md file's version + date + changelog
# - Update the unraid/OpenAI_WebUI.xml file's <Date> and <Changes> sections
# - Commit and push the changes to GitHub (in the branch created at the beginning)
# - On Github, "Open a pull request", 
#   use the version for the release name
#   add PR modifications as a summary of the content of the commits,
#   create the PR, add a self-approve message, merge and delete the branch
# - On the build system, checkout main and pull the changes
#  % git checkout main
#  % git pull
# - Delete the temporary branch
#  % git branch -d branch_name
# - Tag the release on GitHub
#  % git tag version_id
#  % git push origin version_id
# - Create a release on GitHub using the version tag, add the release notes, and publish
# - Delete the created docker builder
#  % make buildx_rm
