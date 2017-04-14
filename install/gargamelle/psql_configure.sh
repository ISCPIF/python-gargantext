#!/bin/bash

#######################################################################
##    ____           _
##   |  _ \ ___  ___| |_ __ _ _ __ ___  ___
##   | |_) / _ \/ __| __/ _` | '__/ _ \/ __|
##   |  __/ (_) \__ \ || (_| | | |  __/\__ \
##   |_|   \___/|___/\__\__, |_|  \___||___/
##                      |___/
#######################################################################
echo "::::: POSTGRESQL :::::"
su postgres -c 'pg_dropcluster 9.4 main --stop'
#done in docker but redoing it
rm -rf /srv/gargandata && mkdir /srv/gargandata && chown postgres:postgres /srv/gargandata
su postgres -c '/usr/lib/postgresql/9.6/bin/initdb -D /srv/gargandata/'
su postgres -c '/usr/lib/postgresql/9.6/bin/pg_ctl -D /srv/gargandata/ -l /srv/gargandata/journal_applicatif start'

su postgres -c 'pg_createcluster -D /srv/gargandata 9.6 main '
su postgres -c 'pg_ctlcluster -D /srv/gargandata 9.6 main start '
su postgres -c 'pg_ctlcluster 9.6 main start'

service postgresql start

su postgres -c "psql -c \"CREATE user gargantua WITH PASSWORD 'C8kdcUrAQy66U'\""
su postgres -c "createdb -O gargantua gargandb"

echo "Postgres configured"
#service postgresql stop
