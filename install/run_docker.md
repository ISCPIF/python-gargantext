#!/usr/bin/bash
#enter the Image
/srv/gargantext/install/docker/enterGargantextImage
#start postgresql
service postgresql start
#change to user
su gargantua
#activate the virtualenv
source /srv/env_3-5/bin/activate
#go to gargantext srv
cd /srv/gargantext/manage.py runserver 0.0.0.0:8000
