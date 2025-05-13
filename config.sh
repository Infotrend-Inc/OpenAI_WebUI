## oaiwui configuration
# loaded by entrypoint.sh as /oaiwui_config.sh
# ... after setting the variables from the command line: will override with the values set here
#
# To use your custom version, duplicate the file and mount it in the container: -v /path/to/your/config.sh:/oaiwui_config.sh
#
# Can be used to set the other command line variables
# Set using: export VARIABLE=value

## Environment variables loaded when passing environment variables from user to user
# Ignore list: variables to ignore when loading environment variables from user to user
export ENV_IGNORELIST="HOME PWD USER SHLVL TERM OLDPWD SHELL _ SUDO_COMMAND HOSTNAME LOGNAME MAIL SUDO_GID SUDO_UID SUDO_USER ENV_IGNORELIST ENV_OBFUSCATE_PART"
# Obfuscate part: part of the key to obfuscate when loading environment variables from user to user, ex: API_KEY, ...
export ENV_OBFUSCATE_PART="TOKEN API KEY"

# Uncomment and set as preferred, see README.md for more details

## User and group id
#export WANTED_UID=1000
#export WANTED_GID=1000
# DO NOT use `id -u` or `id -g` to set the values, use the actual values -- the script is started by oaiwuitoo with 1025/1025

## Verbose mode
# uncomment is enough to enable
#export OAIWUI_VERBOSE="yes"

##### If desired, copy the content of your .env file into this file
##### and mount it in the container: -v /path/to/your/config.sh:/oaiwui_config.sh


# Do not use an exit code, this is loaded by source
