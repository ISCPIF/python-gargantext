#!/usr/bin/bash
/srv/gargantext/install/docker/enterGargantextImage
/srv/gargantext/install/python/configure
/srv/gargantext/install/postgres/configure
service postgresql start
source /srv/env_3-5/bin/activate
python /srv/gargantext/dbmigrate.py
/srv/gargantext/manage.py makemigrations
/srv/gargantext/manage.py migrate
python /srv/gargantext/dbmigrate.py
python /srv/gargantext/dbmigrate.py
python /srv/gargantext/init_accounts.py /srv/gargantext/install/init/account.csv
