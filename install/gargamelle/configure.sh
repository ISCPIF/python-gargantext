#!/bin/bash

PATH="/srv/gargantext/install/gargamelle"
#./folders_configure.sh;
#./psql_configure.sh;
/bin/bash "$PATH/django_configure.sh"; 
/bin/bash -c "Configuration Ok""
