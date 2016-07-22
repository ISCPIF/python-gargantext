#!/bin/bash
##################################################
#             __| |(_) __ _ _ __   __ _  ___
#            / _` || |/ _` | '_ \ / _` |/ _ \
#           | (_| || | (_| | | | | (_| | (_) |
#            \__,_|/ |\__,_|_| |_|\__, |\___/
#                 |__/             |___/
##################################################
#configure django migrations
##################################################



#echo "Starting Postgres"
#/usr/sbin/service postgresql start

/bin/su gargantua -c 'source /env_3-5/bin/activate \
    && ./srv/gargantext/manage.py makemigrations \
    && ./srv/gargantext/manage.py migrate \
    && ./srv/gargantext/dbmigrate.py \
    && ./srv/gargantext/dbmigrate.py \
    && ./srv/gargantext/dbmigrate.py;'

/usr/sbin/service postgresql stop
