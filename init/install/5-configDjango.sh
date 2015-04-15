#!/bin/bash

git checkout stable
source /srv/gargantext_env/bin/activate

cd /srv/gargantext
./manage.py collectstatic

chown -R gargantua:www-data /var/www/gargantext





