###########################################################
# Gargamelle WEB
###########################################################
#Build an image starting with debian:stretch image
# wich contains all the source code of the app
FROM debian:stretch
MAINTAINER ISCPIF <gargantext@iscpif.fr>

USER root

### Update and install base dependencies
RUN echo "############ DEBIAN LIBS ###############"
RUN apt-get update && \
    apt-get install -y \
    apt-utils ca-certificates locales \
    sudo aptitude gcc g++ wget git vim \
    build-essential make \
    postgresql-9.6 postgresql-client-9.6 postgresql-contrib-9.6 \
    postgresql-server-dev-9.6 libpq-dev libxml2 \
    postgresql-9.6 postgresql-client-9.6 postgresql-contrib-9.6


### Configure timezone and locale
RUN echo "###########  LOCALES & TZ #################"
RUN echo "Europe/Paris" > /etc/timezone
ENV TZ "Europe/Paris"

RUN sed -i -e 's/# en_GB.UTF-8 UTF-8/en_GB.UTF-8 UTF-8/' /etc/locale.gen && \
    sed -i -e 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    echo 'LANG="fr_FR.UTF-8"' > /etc/default/locale
ENV LANG fr_FR.UTF-8
ENV LANGUAGE fr_FR.UTF-8
ENV LC_ALL fr_FR.UTF-8


### Install main dependencies and python packages based on Debian distrib
RUN echo "############# PYTHON DEPENDENCIES ###############"
RUN apt-get update && apt-get install -y \
        libxml2-dev xml-core libgfortran-6-dev \
        libpq-dev \
        python3.5 \
        python3-dev \
        # for numpy, pandas and numpyperf
        python3-six python3-numpy python3-setuptools \
        python3-numexpr \
        # python dependencies
        python3-pip \
        # for lxml
        libxml2-dev libxslt-dev \
        libxslt1-dev zlib1g-dev

# UPDATE AND CLEAN
RUN apt-get update && apt-get autoclean &&\
    rm -rf /var/lib/apt/lists/*
#NB: removing /var/lib will avoid to significantly fill up your /var/ folder on your native system

########################################################################
### PYTHON ENVIRONNEMENT (as ROOT)
########################################################################

RUN adduser --disabled-password --gecos "" gargantua

RUN pip3 install virtualenv
RUN virtualenv /env_3-5
RUN echo 'alias venv="source /env_3-5/bin/activate"' >> ~/.bashrc
# CONFIG FILES
ADD requirements.txt /
ADD psql_configure.sh /
ADD django_configure.sh /

RUN . /env_3-5/bin/activate && pip3 install -r requirements.txt && \
    pip3  install git+https://github.com/zzzeek/sqlalchemy.git@rel_1_1 && \
    python3 -m nltk.downloader averaged_perceptron_tagger -d /usr/local/share/nltk_data

RUN chown gargantua:gargantua -R /env_3-5

########################################################################
### POSTGRESQL DATA (as ROOT)
########################################################################

RUN sed -iP "s%^data_directory.*%data_directory = \'\/srv\/gargandata\'%" /etc/postgresql/9.5/main/postgresql.conf
RUN echo "host all  all    0.0.0.0/0  md5" >> /etc/postgresql/9.5/main/pg_hba.conf
RUN echo "listen_addresses='*'" >> /etc/postgresql/9.5/main/postgresql.conf

EXPOSE 5432 8000

# VOLUME ["/srv/",]
