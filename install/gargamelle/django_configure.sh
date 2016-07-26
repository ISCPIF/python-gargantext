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
echo "::::: DJANGO :::::"
#echo "Starting Postgres"
#/usr/sbin/service postgresql start



/bin/su gargantua -c 'source /env_3-5/bin/activate &&\
    echo "Activated env" &&\
    ./srv/gargantext/manage.py makemigrations &&\
    ./srv/gargantext/manage.py migrate && \
    echo "migrations ok" &&\
    ./srv/gargantext/dbmigrate.py && \
    ./srv/gargantext/dbmigrate.py && \
    ./srv/gargantext/dbmigrate.py && \
    ./srv/gargantext/manage.py createsuperuser'

/usr/sbin/service postgresql stop

