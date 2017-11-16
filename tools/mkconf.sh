#!/usr/bin/env bash

USAGE="Usage: $0 [-h|--help] [-f|--force] [dev|prod]"
while :; do
    case $1 in
        -h|--help) echo $USAGE; exit;;
        -f|--force) FORCE=1;;
        --) shift; break;;
        *) break
    esac
    shift
done

# Target can be dev or prod
TARGET="${1:-dev}"

# Gargantext configuration file path
[ -z "$GARGANTEXT_CONF" ] && GARGANTEXT_CONF=gargantext.ini

# Configuration template path
TEMPLATE=tools/conf/gargantext.template.ini

# Check for configuration file existence
if [ -f "$GARGANTEXT_CONF" -a -z "$FORCE" ]; then
    echo -e "Configuration file $GARGANTEXT_CONF already exists, you may" \
            "need to edit it.\nTo generate a new configuration anyway you" \
            "can do: ./tools/mkconf.sh -f $TARGET"
    exit
fi

# Check permissions for configuration file
D=$(dirname $GARGANTEXT_CONF)
if ! (mkdir -p $D && touch $GARGANTEXT_CONF 2>/dev/null); then
    echo "Can't create $GARGANTEXT_CONF, please check permissions."
    exit 1
fi

# Setup DEBUG mode for dev target
[ "$TARGET" = "prod" ] && DEBUG=False || DEBUG=True

echo "Generate secret key for Django..."
SECRET_KEY=$(python ./tools/gensecret.py)

echo "PostgreSQL configuration..."

DB_NAME_DEFAULT=gargandb
DB_USER_DEFAULT=gargantua
DB_HOST=127.0.0.1
DB_PORT=5432

while :; do
    read -p "Database name [$DB_NAME_DEFAULT]: " DB_NAME
    DB_NAME=${DB_NAME:-$DB_NAME_DEFAULT}

    read -p "Database user [$DB_USER_DEFAULT]: " DB_USER
    DB_USER=${DB_USER:-$DB_USER_DEFAULT}

    read -s -p "Please provide the password for $DB_USER: " DB_PASS && echo

    echo "Check database access..."
    if ! sudo -u postgres PGPASSWORD="$DB_PASS" psql -wq -d "$DB_NAME" \
                    -U "$DB_USER" -h 127.0.0.1 -c "" 1>/dev/null 2>&1; then
        read -p "Can't connect to database, give up? (Y/n) " GIVE_UP
        [ -z "$GIVE_UP" -o "${GIVE_UP,,}" = "y" ] && break
    else
        echo "Access granted!"
        break
    fi
done

escape_ini () {
    echo -n "$1" | sed -e 's/[/&\]/\\&/g'
}

# Escape variables
SECRET_KEY=$(escape_ini "$SECRET_KEY")
DB_NAME=$(escape_ini "$DB_NAME")
DB_USER=$(escape_ini "$DB_USER")
DB_PASS=$(escape_ini "$DB_PASS")

echo "Generate configuration file from $TEMPLATE..."
sed -E -e "s/[{]DEBUG[}]/$DEBUG/g" \
       -e "s/[{]SECRET_KEY[}]/$SECRET_KEY/g" \
       -e "s/[{]DB_HOST[}]/$DB_HOST/g" \
       -e "s/[{]DB_PORT[}]/$DB_PORT/g" \
       -e "s/[{]DB_NAME[}]/$DB_NAME/g" \
       -e "s/[{]DB_USER[}]/$DB_USER/g" \
       -e "s/[{]DB_PASS[}]/$DB_PASS/g" \
       "$TEMPLATE" > "$GARGANTEXT_CONF" \
    && echo "Configuration for $TARGET environment written successfully in" \
            "$GARGANTEXT_CONF."

if [ -z "$DB_PASS" ]; then
    echo "You didn't provide any database password, please" \
         "edit $GARGANTEXT_CONF before running Gargantext."
fi
