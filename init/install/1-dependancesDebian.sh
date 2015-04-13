#!/bin/dash

# TODO do apt-get install --force-yes 


apt-get install postgresql
apt-get install postgresql-contrib
apt-get install rabbitmq-server
apt-get install tmux

apt-get install python3.4-venv
#apt-get install python-virtualenv

apt-get install libpng12-dev
apt-get install libpng-dev
apt-get install libfreetype6-dev
apt-get install python-dev
apt-get install libpq-dev
apt-get install libpq-dev

apt-get build-dep python-matplotlib
apt-get install python-matplotlib

#Paquets Debian a installer
# easy_install -U distribute (matplotlib)
#lxml
apt-get install libffi-dev
apt-get install libxml2-dev
apt-get install libxslt1-dev

# ipython readline
apt-get install libncurses5-dev
apt-get install pandoc

# scipy:
apt-get install gfortran
apt-get install libopenblas-dev
apt-get install liblapack-dev

#nlpserver
apt-get install libgflags-dev
aptitude install libgoogle-glog-dev

# MElt
# soon

## SERVER Configuration

# server configuration
apt-get install nginx

# UWSGI with pcre support
apt-get install libpcre3 libpcre3-dev
apt-get install python3-pip
pip3 install uwsgi

