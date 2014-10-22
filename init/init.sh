#!/bin/bash

psql -d gargandb -f init.sql

sleep 2
./manage.py syncdb

sleep 2
./manage.py shell < init.py
