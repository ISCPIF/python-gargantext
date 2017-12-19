#!/usr/bin/env bash

ENV_FILE=.env
ENVIR=${ENVIR:-dev}
DSM=gargantext.settings
GARGANTEXT_CONF=${GARGANTEXT_CONF:-gargantext.ini}
POSTGREST_CONF=${POSTGREST_CONF:-postgrest.conf}

read -r -d '' DJANGO_VAR <<EOF
# Django settings module, it is unlikely that you'll need to change that.
# WARNING: It will be overwritten!
DJANGO_SETTINGS_MODULE=$DSM
EOF

build_env () {
    cat << EOF > $ENV_FILE
# ENVIR can be dev or prod
ENVIR=$ENVIR
$DJANGO_VAR
# Paths of configuration files, you're welcome to change that; when a simple
# filename is given, it'll be searched in current directory.
GARGANTEXT_CONF=$GARGANTEXT_CONF
POSTGREST_CONF=$POSTGREST_CONF
EOF
}

update_env () {
    grep -Eq '^\s*DJANGO_SETTINGS_MODULE=' "$ENV_FILE" \
        && sed -E -i "s/^(\\s*DJANGO_SETTINGS_MODULE=).*/\\1$DSM/g" $ENV_FILE \
        || echo "$DJANGO_VAR" >> "$ENV_FILE"
}

[ -f "$ENV_FILE" ] && update_env || build_env
