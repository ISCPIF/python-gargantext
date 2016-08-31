### Update and install base dependencies
echo "############ DEBIAN LIBS ###############"
apt-get update && \
apt-get install -y \
apt-utils ca-certificates locales \
sudo aptitude gcc g++ wget git vim \
build-essential make \
postgresql-9.5 postgresql-client-9.5 postgresql-contrib-9.5 \
postgresql-server-dev-9.5 libpq-dev libxml2 \
postgresql-9.5 postgresql-client-9.5 postgresql-contrib-9.5 \
nginx rabbitmq-server


### Configure timezone and locale
echo "###########  LOCALES & TZ #################"
echo "Europe/Paris" > /etc/timezone
#ENV TZ "Europe/Paris"

sed -i -e 's/# en_GB.UTF-8 UTF-8/en_GB.UTF-8 UTF-8/' /etc/locale.gen && \
sed -i -e 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen && \
locale-gen && \
update-locale LANG=fr_FR.UTF-8 && \
update-locale LANGUAGE=fr_FR.UTF-8 && \
update-locale LC_ALL=fr_FR.UTF-8
# Not: using LC_ALL is discouraged
# see warning: https://wiki.debian.org/Locale

### Install main dependencies and python packages based on Debian distrib
echo "############# PYTHON DEPENDENCIES ###############"
apt-get update && apt-get install -y \
 libxml2-dev xml-core libgfortran-5-dev \
 libpq-dev \
 python3.5 \
 python3-dev \
 # for numpy, pandas and numpyperf
 python3-six python3-numpy python3-setuptools \
 python3-numexpr \
 # python dependencies
 python3-pip \
 # for lxml
 libxml2-dev libxslt-dev
 #libxslt1-dev zlib1g-dev

# UPDATE AND CLEAN
apt-get update && apt-get autoclean &&\
rm -rf /var/lib/apt/lists/*
#NB: removing /var/lib will avoid to significantly fill up your /var/ folder on your native system

########################################################################
### PYTHON ENVIRONNEMENT (as ROOT)
########################################################################

#adduser --disabled-password --gecos "" gargantua

cd /srv/
pip3 install virtualenv
virtualenv /srv/env_3-5
echo 'alias venv="source /srv/env_3-5/bin/activate"' >> ~/.bashrc
# CONFIG FILES
#ADD requirements.txt /
#ADD psql_configure.sh /
#ADD django_configure.sh /

/srv/env_3-5/bin/activate && pip3 install -r requirements.txt && \
pip3  install git+https://github.com/zzzeek/sqlalchemy.git@rel_1_1 && \
python3 -m nltk.downloader averaged_perceptron_tagger -d /usr/local/share/nltk_data

chown gargantua:gargantua -R /srv/env_3-5

########################################################################
### POSTGRESQL DATA (as ROOT)
########################################################################

sed -iP "s%^data_directory.*%data_directory = \'\/srv\/gargandata\'%" /etc/postgresql/9.5/main/postgresql.conf
echo "host all  all    0.0.0.0/0  md5" >> /etc/postgresql/9.5/main/pg_hba.conf
echo "listen_addresses='*'" >> /etc/postgresql/9.5/main/postgresql.conf

