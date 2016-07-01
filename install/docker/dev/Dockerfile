###########################################################
#     ____             ____           _____   __  ___     #
#    / ___| __ _ _ __ / ___| __ _ _ _|_   _|__\ \/ / |_   #
#   | |  _ / _` | '__| |  _ / _` | '_ \| |/ _ \\  /| __|  #
#   | |_| | (_| | |  | |_| | (_| | | | | |  __//  \| |_   #
#    \____|\__,_|_|   \____|\__,_|_| |_|_|\___/_/\_\\__|  #
#                                                         #
###########################################################
# https://docs.docker.com/compose/django/
######################################################################
FROM debian:stretch
#FROM gargantext
MAINTAINER ISCPIF <alexandre.delanoe@iscpif.fr>
######################################################################

USER root

RUN apt-get update && \
    apt-get install -y \
    apt-utils ca-certificates locales man dialog\
    sudo aptitude gcc g++ wget git postgresql-9.5 vim

### Configure timezone and locale
RUN echo "Europe/Paris" > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata && \
    sed -i -e 's/# en_GB.UTF-8 UTF-8/en_GB.UTF-8 UTF-8/' /etc/locale.gen && \
    sed -i -e 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen && \
    echo 'LANG="fr_FR.UTF-8"' > /etc/default/locale && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=fr_FR.UTF-8

### Install Database, main dependencies and Python
### (installing some Debian version before pip to get dependencies)
RUN apt-get update && apt-get install -y \
       postgresql-server-dev-9.5 libpq-dev libxml2 \
       libxml2-dev xml-core libgfortran-5-dev \
       virtualenv python3-virtualenv \
       python3 python3-dev \
       python3.5 python3.5-dev \
       python3-six python3-numpy python3-setuptools \
       # ^for numpy, pandas
       python3-numexpr \
       # ^ for numpy performance
       libxml2-dev libxslt-dev \
       # ^ for lxml
       bzip2
       # ^ for the Gargantext librairies

### PROD VERSION OF GARGANTEXT ONLY
#RUN apt-get install -y uwsgi nginx  uwsgi-plugin-python rabbitmq-server
#
## ## CREATE USER and adding it to sudo
## ## TODO ask user for password
RUN adduser --disabled-password --gecos "" gargantua

RUN apt-get install -y sudo && adduser gargantua sudo \
     && echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers


#####################################################################
# CONFIGURE POSTGRESQL
#####################################################################

RUN sed -iP "s%^data_directory.*%data_directory = \'\/srv\/gargantext_data\'%" /etc/postgresql/9.5/main/postgresql.conf
#####################################################################

COPY  . /install
CMD [./install/python/configure, ./install/posgres/configure, sudo pip install virtualenvwrapper]




