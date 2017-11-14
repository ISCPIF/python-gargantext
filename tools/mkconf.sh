#!/usr/bin/env bash

# Handle arguments
while getopts f option; do
    case "${option}"
    in
        f) FORCE=1;;
    esac
done

# Gargantext configuration file
[ -z "$GARGANTEXT_CONF" ] && GARGANTEXT_CONF=gargantext.ini

# Configuration template
TEMPLATE=tools/gargantext.template.ini

if [ -f "$GARGANTEXT_CONF" -a -z "$FORCE" ]; then
    echo "Configuration file $GARGANTEXT_CONF already exists. To generate a" \
         "new configuration anyway you can do: ./tools/mkconf.sh -f"
    exit
fi

D=$(dirname $GARGANTEXT_CONF)
if ! (mkdir -p $D && touch $GARGANTEXT_CONF 2>/dev/null); then
    echo "Can't create $GARGANTEXT_CONF, please check permissions."
    exit 1
fi

echo "Generate secret key for Django..."
SECRET_KEY=$(python ./tools/gensecret.py)

echo "PostgreSQL configuration..."

DB_NAME_DEFAULT=gargandb
DB_USER_DEFAULT=gargantua

read -p "Database name [$DB_NAME_DEFAULT]: " DB_NAME
DB_NAME=${DB_NAME:-$DB_NAME_DEFAULT}

read -p "Database user [$DB_USER_DEFAULT]: " DB_USER
DB_USER=${DB_USER:-$DB_USER_DEFAULT}

read -s -p "Please provide the password for $DB_USER: " DB_PASS && echo

SECRET_KEY=$(echo -n "$SECRET_KEY" | sed -e 's/[\\\/&\"]/\\\\&/g')
DB_NAME=$(echo -n "$DB_NAME" | sed -e 's/[\\\/&\"]/\\\\&/g')
DB_USER=$(echo -n "$DB_USER" | sed -e 's/[\\\/&\"]/\\\\&/g')
DB_PASS=$(echo -n "$DB_PASS" | sed -e 's/[\\\/&\"]/\\\\&/g')

echo "Generate configuration file from $TEMPLATE..."
sed -E -e 's/[{]DEBUG[}]/True/g' \
       -e "s/[{]SECRET_KEY[}]/$SECRET_KEY/g" \
       -e "s/[{]DB_NAME[}]/$DB_NAME/g" \
       -e "s/[{]DB_USER[}]/$DB_USER/g" \
       -e "s/[{]DB_PASS[}]/$DB_PASS/g" \
       "$TEMPLATE" > "$GARGANTEXT_CONF" \
    && echo "Configuration written successfully in $GARGANTEXT_CONF."

[ -z "$DB_PASS" ] && echo "You didn't provide any database password, please" \
                          "edit $GARGANTEXT_CONF before running Gargantext."
