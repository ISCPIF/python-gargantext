#!/usr/bin/env bash

ENV_FILE=.env

read -r -d '' DJANGO_VAR <<EOF
# Django settings module, it is unlikely that you'll need to change that
DJANGO_SETTINGS_MODULE=gargantext.settings
EOF

build_env () {
    cat << EOF > $ENV_FILE
$DJANGO_VAR
# Path to gargantext configuration file, you're welcome to change that; when
# a simple filename is given, it'll be searched in current directory
GARGANTEXT_CONF=gargantext.ini
EOF
}

update_env () {
    grep -Eq '^\s*DJANGO_SETTINGS_MODULE\s*=' "$ENV_FILE" || echo "$DJANGO_VAR" >> "$ENV_FILE"
}

[ -f "$ENV_FILE" ] && update_env || build_env
