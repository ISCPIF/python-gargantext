#!/bin/bash

#MAINTAINER ISCPIF <alexandre.delanoe@iscpif.fr>

apt-get update && \
apt-get install -y \
apt-utils ca-certificates locales \
sudo aptitude gcc g++ wget git postgresql-9.5 vim

### Configure timezone and locale
echo "Europe/Paris" > /etc/timezone && \
   dpkg-reconfigure -f noninteractive tzdata && \
   sed -i -e 's/# en_GB.UTF-8 UTF-8/en_GB.UTF-8 UTF-8/' /etc/locale.gen && \
   sed -i -e 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen && \
   echo 'LANG="fr_FR.UTF-8"' > /etc/default/locale && \
   dpkg-reconfigure --frontend=noninteractive locales && \
   update-locale LANG=fr_FR.UTF-8


## PROD VERSION OF GARGANTEXt
apt-get install -y uwsgi nginx 


### CREATE USER and adding it to sudo
## USER gargantua cannot not connect with password but SSH key
adduser --disabled-password --gecos "" gargantua \
   && adduser gargantua sudo \
   && echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers 

# addgroup gargantext here with specific users

## Install Database, main dependencies and Python
## (installing some Debian version before pip to get dependencies)
apt-get update && apt-get install -y \
   postgresql-server-dev-9.5 libpq-dev libxml2 \
   libxml2-dev xml-core libgfortran-5-dev \
   virtualenv python3-virtualenv \
   python3.4 python3.4-dev \
   python3.5 python3.5-dev \
   python3-six python3-numpy python3-setuptools \ # for numpy, pandas
   python3-numexpr \                              # for numpy performance
   libxml2-dev libxslt-dev                        # for lxml


#if [[ -e "/srv/gargantext" ]]
#rm -rf /srv/gargantext /srv/env_3-5

for dir in "/srv/gargantext"\
           "/srv/gargantext_lib"\
           "/srv/env_3-5"\
           "/var/www/gargantext"; do \
    mkdir $dir
    chown gargantua:gargantua $dir
done

echo "Root: END of the installation of Gargantext by Root."

