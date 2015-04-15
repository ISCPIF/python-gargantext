#!/bin/dash

# TODO do apt-get install --force-yes --force-yes 


apt-get install --force-yes postgresql
apt-get install --force-yes postgresql-contrib
apt-get install --force-yes rabbitmq-server
apt-get install --force-yes tmux
apt-get install --force-yes uwsgi uwsgi-plugin-python3

apt-get install --force-yes python3.4-venv
#apt-get install --force-yes python-virtualenv

apt-get install --force-yes libpng12-dev
apt-get install --force-yes libpng-dev
apt-get install --force-yes libfreetype6-dev
apt-get install --force-yes python-dev
apt-get install --force-yes libpq-dev
apt-get install --force-yes libpq-dev

#apt-get build-dep python-matplotlib
#apt-get install --force-yes python-matplotlib

#Paquets Debian a installer
# easy_install --force-yes -U distribute (matplotlib)
#lxml
apt-get install --force-yes libffi-dev
apt-get install --force-yes libxml2-dev
apt-get install --force-yes libxslt1-dev

# ipython readline
apt-get install --force-yes libncurses5-dev
apt-get install --force-yes pandoc

# scipy:
apt-get install --force-yes gfortran
apt-get install --force-yes libopenblas-dev
apt-get install --force-yes liblapack-dev

#nlpserver
apt-get install --force-yes libgflags-dev
aptitude install --force-yes libgoogle-glog-dev

# MElt
# soon

## SERVER Configuration

# server configuration
apt-get install --force-yes nginx

# UWSGI with pcre support
apt-get install --force-yes libpcre3 libpcre3-dev
apt-get install --force-yes python3-pip
pip3 install --force-yes uwsgi

