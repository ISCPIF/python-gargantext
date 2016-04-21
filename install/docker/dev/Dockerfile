###########################################################
#     ____             ____           _____   __  ___     #
#    / ___| __ _ _ __ / ___| __ _ _ _|_   _|__\ \/ / |_   #
#   | |  _ / _` | '__| |  _ / _` | '_ \| |/ _ \\  /| __|  #
#   | |_| | (_| | |  | |_| | (_| | | | | |  __//  \| |_   #
#    \____|\__,_|_|   \____|\__,_|_| |_|_|\___/_/\_\\__|  #
#                                                         #
###########################################################

######################################################################
FROM debian:stretch
#FROM gargantext
MAINTAINER ISCPIF <alexandre.delanoe@iscpif.fr>
######################################################################

USER root

RUN apt-get update && \
    apt-get install -y \
    apt-utils ca-certificates locales \
    sudo aptitude gcc g++ wget git postgresql-9.5 vim

## Configure timezone and locale
RUN echo "Europe/Paris" > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata && \
    sed -i -e 's/# en_GB.UTF-8 UTF-8/en_GB.UTF-8 UTF-8/' /etc/locale.gen && \
    sed -i -e 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen && \
    echo 'LANG="fr_FR.UTF-8"' > /etc/default/locale && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=fr_FR.UTF-8

## Install Database, main dependencies and Python
## (installing some Debian version before pip to get dependencies)
RUN apt-get update && apt-get install -y \
       postgresql-server-dev-9.5 libpq-dev libxml2 \
       libxml2-dev xml-core libgfortran-5-dev \
       virtualenv python3-virtualenv \
       python3.4 python3.4-dev \
       python3.5 python3.5-dev \
       python3-six python3-numpy python3-setuptools \
       # ^for numpy, pandas
       python3-numexpr \
       # ^ for numpy performance
       libxml2-dev libxslt-dev
       # ^ for lxml

## PROD VERSION OF GARGANTEXT ONLY
#RUN apt-get install -y uwsgi nginx  uwsgi-plugin-python rabbitmq-server

# ## CREATE USER and adding it to sudo
# ## TODO ask user for password
RUN adduser --disabled-password --gecos "" gargantua
RUN apt-get install -y sudo && adduser gargantua sudo \
     && echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers


# FIXME, it depends on postgres configuration
VOLUME ["/srv","/var"]

# Create directories in /srv
# FIXME: not tested
RUN for dir in "/srv/gargantext"\
           "/srv/gargantext_lib"\
           "/srv/gargantext_static"\
           "/srv/gargantext_media"\
           "/srv/env_3-5"\
           "/var/www/gargantext"; do \
    mkdir -p $dir ;\
    chown gargantua:gargantua $dir ; \
    done ;\
    echo "Root: END of the installation of Gargantext by Root." ;


######################################################################
## CONFIGURE POSTGRESQL
######################################################################
USER postgres

RUN /etc/init.d/postgresql start &&\ 
    psql -c "CREATE user gargantua WITH PASSWORD 'C8kdcUrAQy66U'" &&\
    createdb -O gargantua gargandb \
    && echo "Root: END of the installation of Gargantexts Database by postgres."


######################################################################
## INSTALL MAIN DEPENDENCIES
######################################################################
#USER gargantua
#
#
## Installing pip version of python libs
## Possible FIXME : if `pip install -r requirements.txt` fails
##                  then: fixme >> maybe (split the list)
##                  else: enjoy
#
## TODO: user local file requirements with docker (and not wget)
#
#RUN wget http://dl.delanoe.org/requirements.txt -o /tmp/requirements.txt \
#      && /usr/bin/virtualenv --py=/usr/bin/python3.5 env_3-5 \
#      && /bin/bash -c 'source env_3-5/bin/activate' \
#      && /bin/bash -c 'env_3-5/bin/pip install git+https://github.com/zzzeek/sqlalchemy.git@rel_1_1' \
#      && /bin/bash -c 'env_3-5/bin/pip install -r /tmp/requirements.txt'
#

## GET CONFIG FILES (need update)
#WORKDIR /tmp
#RUN wget http://dl.gargantext.org/gargantext_lib.tar.bz2 \
#     && tar xvjf gargantext_lib.tar.bz2 -o /srv/gargantext_lib \
#     && chown -R gargantua:gargantua /srv/gargantext_lib \
#     && echo "Root: END of the installation of Gargantexts Database by postgres."

# TODO script pour peupler la base 

######################################################################
# Last step as user:
## TODO (soon) : git clone https://gogs.iscpif.fr/gargantext.git
#RUN git clone ssh://gitolite@delanoe.org:1979/gargantext /srv/gargantext \
#	&& cd /srv/gargantext \
#	&& git fetch origin refactoring \
#	&& git checkout refactoring


######################################################################
