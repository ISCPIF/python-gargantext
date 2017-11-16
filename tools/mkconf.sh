#!/usr/bin/env bash

query () {
    PGPASSWORD="$2" psql -w -d "$DB_NAME" -U "$1" -h "$DB_HOST" -p "$DB_PORT" \
                         -c "$3" 1>/dev/null 2>&1
}

escape_ini () {
    echo -n "$1" | sed -e 's/[/&\]/\\&/g'
}

# Adapted from https://gist.github.com/cdown/1163649
escape_url () {
    local _LC_COLLATE=$LC_COLLATE
    LC_COLLATE=C

    local length="${#1}"
    for (( i = 0; i < length; i++ )); do
        local c="${1:i:1}"
        case $c in
            [a-zA-Z0-9.~_-]) printf "$c" ;;
            *) printf '%%%02X' "'$c" ;;
        esac
    done

    LC_COLLATE=$_LC_COLLATE
}

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

# PostgREST configuration file path
[ -z "$POSTGREST_CONF" ] && POSTGREST_CONF=postgrest.conf

# Configuration template paths
GARGANTEXT_TEMPLATE=tools/conf/gargantext.template.ini
POSTGREST_TEMPLATE=tools/conf/postgrest.template.conf

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

echo "▸ Generate secret key for Django..."
SECRET_KEY=$(pipenv run python ./tools/gensecret.py 2>/dev/null)

echo "▸ PostgreSQL configuration..."

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
    if query "$DB_USER" "$DB_PASS" ""; then
        DB_ACCESS=true
        echo "Access granted!"
        break
    else
        DB_ACCESS=false
        read -p "Can't connect to database, give up? (Y/n) " GIVE_UP
        [ -z "$GIVE_UP" -o "${GIVE_UP,,}" = "y" ] && break
    fi
done

echo "▸ PostgresREST configuration..."

PGREST_USER=authenticator
PGREST_PASS=CHANGEME

if $DB_ACCESS && query "$PGREST_USER" "$PGREST_PASS" ""; then
    read -p "You should change password for database user $PGREST_USER, auto-generate a new one? (Y/n) " PGREST_CHANGE
    # Generate a password with letters and digits between 12 and 20 chars
    PGREST_PASS=$(pipenv run python ./tools/gensecret.py LD 12 20 2>/dev/null)
    if [ "${PGREST_CHANGE,,}" = "y" ]; then
        query "$DB_USER" "$DB_PASS" "ALTER ROLE $PGREST_USER PASSWORD '$PGREST_PASS'"
    fi
fi

PGREST_DB_URI="postgres://"$(escape_url "$PGREST_USER")":"$(escape_url "$PGREST_PASS")"@"$(escape_url "$DB_HOST")":"$(escape_url "$DB_PORT")"/"$(escape_url "$DB_NAME")

# Escape variables
SECRET_KEY=$(escape_ini "$SECRET_KEY")
DB_HOST=$(escape_ini "${DB_HOST:-127.0.0.1}")
DB_PORT=$(escape_ini "${DB_PORT:-5432}")
DB_NAME=$(escape_ini "$DB_NAME")
DB_USER=$(escape_ini "$DB_USER")
DB_PASS=$(escape_ini "$DB_PASS")
PGREST_DB_URI=$(escape_ini "$PGREST_DB_URI")

echo "▸ Generate configuration file from $GARGANTEXT_TEMPLATE..."
sed -E -e "s/[{]DEBUG[}]/$DEBUG/g" \
       -e "s/[{]SECRET_KEY[}]/$SECRET_KEY/g" \
       -e "s/[{]DB_HOST[}]/$DB_HOST/g" \
       -e "s/[{]DB_PORT[}]/$DB_PORT/g" \
       -e "s/[{]DB_NAME[}]/$DB_NAME/g" \
       -e "s/[{]DB_USER[}]/$DB_USER/g" \
       -e "s/[{]DB_PASS[}]/$DB_PASS/g" \
       "$GARGANTEXT_TEMPLATE" > "$GARGANTEXT_CONF" \
    && echo "Configuration for $TARGET environment written successfully in" \
            "$GARGANTEXT_CONF."

echo "▸ Generate configuration file for PostgREST from $POSTGREST_TEMPLATE..."
sed -E -e "s/[{]DB_URI[}]/$PGREST_DB_URI/g" \
       -e "s/[{]SECRET_KEY[}]/$SECRET_KEY/g" \
       "$POSTGREST_TEMPLATE" > "$POSTGREST_CONF" \
    && echo "PostgREST configuration written successfully in $POSTGREST_CONF."

if [ -z "$DB_PASS" ]; then
    echo "WARNING: You didn't provide any database password, please" \
         "edit $GARGANTEXT_CONF before running Gargantext."
fi

if ! $DB_ACCESS; then
    echo "WARNING: Couldn't configure PostgREST user $PGREST_USER correctly," \
         "you may need to edit $POSTGREST_CONF manually."
fi
