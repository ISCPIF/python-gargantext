#/bin/bash


## Quick Manual
## Install docker.io && sudo
## sudo docker build -t gargantext .
## docker run -i -t gargantext /bin/bash

# Install Docker
# Debian/Ubuntu: apt-get install docker

# run turboparser port, with python 3.4
#docker run -d -p 8000:8000 -v /srv:/srv -t gargantext python /srv/gargantext/gargantext.py


#######################################################################

#sudo adduser --disabled-password --gecos "" gargantua

### Create directories in /srv
### FIXME: not tested
#for dir in "/srv/gargantext"\
#           "/srv/gargantext_lib"\
#           "/srv/gargantext_static"\
#           "/srv/gargantext_media"\
#           "/srv/gargantext_data"\
#           "/srv/env_3-5"\
#           "/var/www/gargantext"; do \
#    sudo mkdir -p $dir ;\
#    sudo chown gargantua:gargantua $dir ; \
#done
#
#######################################################################
## Last step as user:
### TODO (soon) : git clone https://gogs.iscpif.fr/gargantext.git
#git clone ssh://gitolite@delanoe.org:1979/gargantext /srv/gargantext \
#    && cd /srv/gargantext \
#    && git fetch origin refactoring \
#    && git checkout refactoring
#

######################################################################
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


######################################################################
#    ____           _                      
#   |  _ \ ___  ___| |_ __ _ _ __ ___  ___ 
#   | |_) / _ \/ __| __/ _` | '__/ _ \/ __|
#   |  __/ (_) \__ \ || (_| | | |  __/\__ \
#   |_|   \___/|___/\__\__, |_|  \___||___/
#                      |___/               
######################################################################
# 
# sudo chown -R postgres:postgres /srv/gargantext_data/ \
# su postgres -c  '/usr/lib/postgresql/9.5/bin/initdb -D /srv/gargantext_data/'
# 
# sudo /etc/init.d/postgresql start \
#     && psql -c "CREATE user gargantua WITH PASSWORD 'C8kdcUrAQy66U'" \
#     && createdb -O gargantua gargandb \
#     && echo "Root: END of the installation of Gargantexts Database by postgres."
# 


######################################################################
#    _     _ _               _      _           
#   | |   (_) |__  _ __ __ _(_)_ __(_) ___  ___ 
#   | |   | | '_ \| '__/ _` | | '__| |/ _ \/ __|
#   | |___| | |_) | | | (_| | | |  | |  __/\__ \
#   |_____|_|_.__/|_|  \__,_|_|_|  |_|\___||___/
#                                               
######################################################################


######################################################################
## INSTALL MAIN DEPENDENCIES
######################################################################
#USER gargantua
##
##
### Installing pip version of python libs
#WORKDIR /home/gargantua
#
#RUN /usr/bin/virtualenv --py=/usr/bin/python3.5 /srv/env_3-5 \
#    && /bin/bash -c 'source /srv/env_3-5/bin/activate' \
#    && /bin/bash -c '/srv/env_3-5/bin/pip install git+https://github.com/zzzeek/sqlalchemy.git@rel_1_1' \
#    && /bin/bash -c '/srv/env_3-5/bin/pip install -r /srv/gargantext/install/python/requirements.txt'
#
# TODO script pour peupler la base 


## GET CONFIG FILES (need update)
#wget http://dl.gargantext.org/gargantext_lib.tar.bz2 \
#     && tar xvjf gargantext_lib.tar.bz2 -o /srv/gargantext_lib \
#     && chown -R gargantua:gargantua /srv/gargantext_lib \
#     && echo "Libs installed"
#
