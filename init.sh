#!/bin/bash

psql -d gargandb -f database_zero.sql
./manage.py syncdb
./manage.py shell < init.py
