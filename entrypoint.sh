#!/bin/bash

set -e

# everyone can read our files by default
umask 0022

# Reorder to have scripts available to one another
error_exit() {
  echo -n "!! ERROR: "
  echo $*
  echo "!! Exiting script (ID: $$)"
  exit 1
}

# Write a world-writeable file (preferably inside /tmp -- ie within the container)
write_worldtmpfile() {
  tmpfile=$1
  if [ -z "${tmpfile}" ]; then error_exit "write_worldfile: missing argument"; fi
  if [ -f $tmpfile ]; then sudo rm -f $tmpfile; fi
  echo -n $2 > ${tmpfile}
  sudo chmod 777 ${tmpfile}
}

# Set verbose mode
if [ ! -z "${OAIWUI_VERBOSE+x}" ]; then write_worldtmpfile /tmp/.OAIWUI-VERBOSE "yes"; fi

verb_echo() {
  if [ -f /tmp/.OAIWUI-VERBOSE ]; then
    echo $*
  fi
}

ok_exit() {
  verb_echo $*
  verb_echo "++ Exiting script (ID: $$)"
  exit 0
}

# Load config (must have at least ENV_IGNORELIST and ENV_OBFUSCATE_PART set)
it=/oaiwui_config.sh
if [ -f $it ]; then
  source $it || error_exit "Failed to load config: $it"
else
  error_exit "Failed to load config: $it not found"
fi
# Check for ENV_IGNORELIST and ENV_OBFUSCATE_PART
if [ -z "${ENV_IGNORELIST+x}" ]; then error_exit "ENV_IGNORELIST not set"; fi
if [ -z "${ENV_OBFUSCATE_PART+x}" ]; then error_exit "ENV_OBFUSCATE_PART not set"; fi

save_env() {
  tosave=$1
  verb_echo "-- Saving environment variables to $tosave"
  env | sort > "$tosave"
}

load_env() {
  tocheck=$1
  overwrite_if_different=$2
  ignore_list="${ENV_IGNORELIST}"
  obfuscate_part="${ENV_OBFUSCATE_PART}"
  if [ -f "$tocheck" ]; then
    echo "-- Loading environment variables from $tocheck (overwrite existing: $overwrite_if_different) (ignorelist: $ignore_list) (obfuscate: $obfuscate_part)"
    while IFS='=' read -r key value; do
      doit=false
      # checking if the key is in the ignorelist
      for i in $ignore_list; do
        if [[ "A$key" ==  "A$i" ]]; then doit=ignore; break; fi
      done
      if [[ "A$doit" == "Aignore" ]]; then continue; fi
      rvalue=$value
      # checking if part of the key is in the obfuscate list
      doobs=false
      for i in $obfuscate_part; do
        if [[ "A$key" == *"$i"* ]]; then doobs=obfuscate; break; fi
      done
      if [[ "A$doobs" == "Aobfuscate" ]]; then rvalue="**OBFUSCATED**"; fi

      if [ -z "${!key}" ]; then
        echo "  ++ Setting environment variable $key [$rvalue]"
        doit=true
      elif [ "$overwrite_if_different" = true ]; then
        cvalue="${!key}"
        if [[ "A${doobs}" == "Aobfuscate" ]]; then cvalue="**OBFUSCATED**"; fi
        if [[ "A${!key}" != "A${value}" ]]; then
          echo "  @@ Overwriting environment variable $key [$cvalue] -> [$rvalue]"
          doit=true
        else
          echo "  == Environment variable $key [$rvalue] already set and value is unchanged"
        fi
      fi
      if [[ "A$doit" == "Atrue" ]]; then
        export "$key=$value"
      fi
    done < "$tocheck"
  fi
}


whoami=`whoami`
script_dir=$(dirname $0)
script_name=$(basename $0)
verb_echo ""; verb_echo ""
verb_echo "======================================"
verb_echo "=================== Starting script (ID: $$)"
verb_echo "== Running ${script_name} in ${script_dir} as ${whoami}"
script_fullname=$0
verb_echo "  - script_fullname: ${script_fullname}"
verb_echo "======================================"

# Get user and group id
if [ -f /tmp/.OAIWUI-WANTED_UID ]; then WANTED_UID=$(cat /tmp/.OAIWUI-WANTED_UID); fi
if [ -f /tmp/.OAIWUI-WANTED_GID ]; then WANTED_GID=$(cat /tmp/.OAIWUI-WANTED_GID); fi
# if no WANTED_UID or WANTED_GID is set, we will set them to 0 (ie root) [the previous default]
WANTED_UID=${WANTED_UID:-0}
WANTED_GID=${WANTED_GID:-0}
# save the values
if [ ! -f /tmp/.OAIWUI-WANTED_UID ]; then write_worldtmpfile /tmp/.OAIWUI-WANTED_UID ${WANTED_UID}; fi
if [ ! -f /tmp/.OAIWUI-WANTED_GID ]; then write_worldtmpfile /tmp/.OAIWUI-WANTED_GID ${WANTED_GID}; fi

# Extracting the command line arguments (if any)(streamlit overrides for example) and placing them in /oaiwui_run.sh
if [ ! -z "$*" ]; then write_worldtmpfile /tmp/oaiwui-run.sh "$*"; fi

# Check user id and group id
new_gid=`id -g`
new_uid=`id -u`
verb_echo "== user ($whoami)"
verb_echo "  uid: $new_uid / WANTED_UID: $WANTED_UID"
verb_echo "  gid: $new_gid / WANTED_GID: $WANTED_GID"

# oaiwuitoo is a specfiic user not existing by default on debian, we can check its whomai
if [ "A${whoami}" == "Aoaiwuitoo" ]; then 
  verb_echo "-- Running as oaiwuitoo, will switch oaiwui to the desired UID/GID"
  # The script is started as oaiwuitoo -- UID/GID 1025/1025

  # We are altering the UID/GID of the oaiwui user to the desired ones and restarting as oaiwui
  # using usermod for the already create oaiwui user, knowing it is not already in use
  # per usermod manual: "You must make certain that the named user is not executing any processes when this command is being executed"

  verb_echo "-- Setting owner of /home/oaiwui to $WANTED_UID:$WANTED_GID (might take a while)"
  sudo chown -R ${WANTED_UID}:${WANTED_GID} /home/oaiwui || error_exit "Failed to set owner of /home/oaiwui"
  verb_echo "-- Setting GID of oaiwui user to $WANTED_GID"
  sudo groupmod -o -g ${WANTED_GID} oaiwui || error_exit "Failed to set GID of oaiwui user"
  verb_echo "-- Setting UID of oaiwui user to $WANTED_UID"
  sudo usermod -o -u ${WANTED_UID} oaiwui || error_exit "Failed to set UID of oaiwui user"

  # save the current environment
  save_env /tmp/.oaiwuitoo-env

  # restart the script as oaiwui set with the correct UID/GID this time
  verb_echo "-- Restarting as oaiwui user with UID ${WANTED_UID} GID ${WANTED_GID}"
  sudo su oaiwui $script_fullname || error_exit "subscript failed"
  ok_exit "Clean exit"
fi

# If we are here, the script is started as another user than oaiwuitoo
# because the whoami value for the oaiwui user can be any existing user, we can not check against it
# instead we check if the UID/GID are the expected ones
if [ "$WANTED_GID" != "$new_gid" ]; then error_exit "oaiwui MUST be running as UID ${WANTED_UID} GID ${WANTED_GID}, current UID ${new_uid} GID ${new_gid}"; fi
if [ "$WANTED_UID" != "$new_uid" ]; then error_exit "oaiwui MUST be running as UID ${WANTED_UID} GID ${WANTED_GID}, current UID ${new_uid} GID ${new_gid}"; fi

# We are therefore running as oaiwui
verb_echo ""; verb_echo "== Running as oaiwui"

# Load environment variables one by one if they do not exist from /tmp/.oaiwuitoo-env
it=/tmp/.oaiwuitoo-env
if [ -f $it ]; then
  load_env $it true
fi

# Extend PATH with the venv bin directory (for python3 and streamlit)
export PATH="/app/.venv/bin:$PATH"

########## 'oaiwui' specific section below
if [ -f /tmp/oaiwui-run.sh ]; then
  sudo chmod +x /tmp/oaiwui-run.sh || error_exit "Failed to make /tmp/oaiwui-run.sh executable"
  /tmp/oaiwui-run.sh
else
  streamlit run OAIWUI_WebUI.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=False --logger.level=info
fi

exit 0
