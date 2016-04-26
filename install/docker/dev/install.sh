#!/bin/bash

# Main user of Gargantext is Gargantua (role of Pantagruel soon)!
#sudo adduser --disabled-password --gecos "" gargantua

#######################################################################
#    ____             _             
#   |  _ \  ___   ___| | _____ _ __ 
#   | | | |/ _ \ / __| |/ / _ \ '__|
#   | |_| | (_) | (__|   <  __/ |   
#   |____/ \___/ \___|_|\_\___|_|   
#                                   
######################################################################

sudo docker build -t gargantext .
# OR
# cd /tmp
# wget http://dl.gargantext.org/gargantext_docker_image.tar \
# && sudo docker import - gargantext:latest < gargantext_docker_image.tar

function do_cker {
    #sudo docker run -d -p 8000:8000 \
    sudo docker run -d \
                   -v /srv2:/srv \
                   -v /home/alexandre:/home/alexandre \
                   -t gargantext:latest \
                   /bin/bash $1
    }


#######################################################################
#    _____     _     _               
#   |  ___|__ | | __| | ___ _ __ ___ 
#   | |_ / _ \| |/ _` |/ _ \ '__/ __|
#   |  _| (_) | | (_| |  __/ |  \__ \
#   |_|  \___/|_|\__,_|\___|_|  |___/
#                                    
#######################################################################

### Create directories in /srv
# Linux only
function create_folders {
    for dir in "/srv/gargantext"\
           "/srv/gargantext_lib"\
           "/srv/gargantext_static"\
           "/srv/gargantext_media"\
           "/srv/gargantext_data"\
           "/srv/env_3-5"; do \
    sudo mkdir -p $dir ;\
    sudo chown gargantua:gargantua $dir ; \
done \
sudo chown -R postgres:postgres /srv/gargantext_data/ 
}

#do_cker "create_folders"


function git_config {
    ### TODO (soon) : git clone https://gogs.iscpif.fr/gargantext.git
    git clone ssh://gitolite@delanoe.org:1979/gargantext /srv/gargantext \
        && cd /srv/gargantext \
        && git fetch origin refactoring \
        && git checkout refactoring
}

#su gargantua -c git_config

#######################################################################
##    ____           _                      
##   |  _ \ ___  ___| |_ __ _ _ __ ___  ___ 
##   | |_) / _ \/ __| __/ _` | '__/ _ \/ __|
##   |  __/ (_) \__ \ || (_| | | |  __/\__ \
##   |_|   \___/|___/\__\__, |_|  \___||___/
##                      |___/               
#######################################################################

function postgres_config {
    /usr/lib/postgresql/9.5/bin/initdb -D /srv/gargantext_data/
}
#do_cker "su postgres -c postgres_config"

function postgres_create_db {
    sudo /etc/init.d/postgresql start \
     && psql -c "CREATE user gargantua WITH PASSWORD 'C8kdcUrAQy66U'" \
     && createdb -O gargantua gargandb \
     && echo "Root: END of the installation of Gargantexts Database by postgres."
} 
#do_cker postgres_create_db 

#######################################################################
##    _     _ _               _      _           
##   | |   (_) |__  _ __ __ _(_)_ __(_) ___  ___ 
##   | |   | | '_ \| '__/ _` | | '__| |/ _ \/ __|
##   | |___| | |_) | | | (_| | | |  | |  __/\__ \
##   |_____|_|_.__/|_|  \__,_|_|_|  |_|\___||___/
##                                               
#######################################################################
#
#######################################################################
### INSTALL MAIN DEPENDENCIES
#######################################################################
###
#### Installing pip version of python libs
#
function install_python_env {
    /usr/bin/virtualenv --py=/usr/bin/python3.5 /srv/env_3-52 \
    && /bin/bash -c 'source /srv/env_3-52/bin/activate' \
    && /bin/bash -c '/srv/env_3-52/bin/pip install git+https://github.com/zzzeek/sqlalchemy.git@rel_1_1' \
    && /bin/bash -c '/srv/env_3-52/bin/pip install -r /srv/gargantext/install/python/requirements.txt'
}

#do_cker "su gargantua -c install_python_env"

#######################################################################
function init_gargantext {
    echo "TODO script pour peupler la base"
}

#do_cker "su gargantua -c init_gargantext"
#######################################################################
### GET CONFIG FILES

function get_libs {
    wget http://dl.gargantext.org/gargantext_lib.tar.bz2 \
     && tar xvjf gargantext_lib.tar.bz2 -o /srv/gargantext_lib \
     && sudo chown -R gargantua:gargantua /srv/gargantext_lib \
     && echo "Libs installed"
    }

#do_cker get_libs

