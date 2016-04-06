#FROM debian:stretch
FROM gargantext
#MAINTAINER ISCPIF <alexandre.delanoe@iscpif.fr>
#
## Install docker.io
## Install sudo
## wget http://dl.gargantext.
## cd /srv/gargantext/install
## sudo docker build -t gargantext .
# docker run -i -t gargantext /bin/bash

USER root

# RUN apt-get update && \
#     apt-get install -y \
#     apt-utils ca-certificates locales \
#     sudo aptitude gcc wget git postgresql-9.5 vim
# 
# ## Configure timezone and locale
# RUN echo "Europe/Paris" > /etc/timezone && \
#     dpkg-reconfigure -f noninteractive tzdata && \
#     sed -i -e 's/# en_GB.UTF-8 UTF-8/en_GB.UTF-8 UTF-8/' /etc/locale.gen && \
#     sed -i -e 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen && \
#     echo 'LANG="fr_FR.UTF-8"' > /etc/default/locale && \
#     dpkg-reconfigure --frontend=noninteractive locales && \
#     update-locale LANG=fr_FR.UTF-8
# 
# 
# RUN apt-get update \
#     && apt-get install -y postgresql-server-dev-9.5 \
#     libpq-dev libxml2 libxml2-dev xml-core libgfortran-5-dev
# 
# # PROD VERSION OF GARGANTEXt
# # RUN apt-get install uwsgi nginx 
# 
# 
# ## CREATE USER and adding it to sudo
# ## TODO ask user for password
# RUN adduser --disabled-password --gecos "" gargantua
# RUN apt-get install -y sudo && adduser gargantua sudo \
#     && echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers 
# 
# # Python dependencies 
# # (installing Debian version before pip to get dependencies)
# # TODO: update it with requirements.txt
# RUN apt-get update && apt-get install -y \
#     virtualenv python3-virtualenv \
# 	python3.4 python3.4-dev \
# 	python3.5 python3.5-dev \
#     python3-six python3-numpy
# 

# # Installing pip version of python libs
WORKDIR /home/gargantua

# FIXME : pip install -r all requirements does not work, need to split the list
#RUN wget http://dl.delanoe.org/requirements.txt \
#    && /usr/bin/virtualenv --py=/usr/bin/python3.5 env_3-5 \
#    && /bin/bash -c 'source env_3-5/bin/activate' \
#    && /bin/bash -c 'env_3-5/bin/pip install git+https://github.com/zzzeek/sqlalchemy.git@rel_1_1' \
#    && /bin/bash -c 'env_3-5/bin/pip install -r requirements.txt'

# chown gargantua




#
## CONFIGURE POSTGRESQL
#

#VOLUME ["/home/gargantua","/data/gargantext"]

## INSTALL MAIN DEPENDENCIES

#WORKDIR /srv
#RUN mkdir -p gargantext


# configure postgres here
# OK
USER postgres
RUN /etc/init.d/postgresql start &&\ 
    psql -c "CREATE user gargantua WITH PASSWORD 'C8kdcUrAQy66U'" &&\
    createdb -O gargantua gargandb


# GET CONFIG FILES
# USER gargantua
#RUN wget http://dl.delanoe.org/gargantext_big.txt -o /srv/gargantext_big.txt
#RUN cd /srv/ && git clone https://gogs.iscpif.fr/gargantext.git


# script pour peupler la base 

# mount /srv
# execute

##################### INSTALLATION END #####################

# Expose the default port
#EXPOSE 54332

# Default port to execute the entrypoint (MongoDB)
#CMD ["--port 27017"]

# Set default container command
#ENTRYPOINT usr/bin/mongod
# ENTRYPOINT /etc/init.d/postgresql start


