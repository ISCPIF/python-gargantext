#!/bin/bash

psql -d gargandb -f init.sql

sleep 2
../manage.py syncdb
psql -d gargandb -f init2.sql


sleep 2
#../manage.py shell < init.py
../manage.py shell < ../init_gargantext.py

#psql -d gargandb -f hstore2jsonb.sql
