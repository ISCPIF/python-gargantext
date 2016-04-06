#!/bin/dash

# TODO do apt-get install --force-yes --force-yes 

#postgresql3.4-server-dev
#+libxml2-dev

sudo apt-get install --force-yes postgresql
sudo apt-get install --force-yes postgresql-contrib
sudo apt-get install --force-yes rabbitmq-server
sudo apt-get install --force-yes tmux
sudo apt-get install --force-yes uwsgi uwsgi-plugin-python3

#apt-get install --force-yes python-virtualenv

sudo apt-get install --force-yes libpng12-dev
sudo apt-get install --force-yes libpng-dev
sudo apt-get install --force-yes libfreetype6-dev
sudo apt-get install --force-yes python-dev
sudo apt-get install --force-yes libpq-dev
sudo apt-get install --force-yes libpq-dev

#apt-get build-dep python-matplotlib
#apt-get install --force-yes python-matplotlib

#Paquets Debian a installer
# easy_install --force-yes -U distribute (matplotlib)
#lxml
sudo apt-get install --force-yes libffi-dev
sudo apt-get install --force-yes libxml2-dev
sudo apt-get install --force-yes libxslt1-dev

# ipython readline
sudo apt-get install --force-yes libncurses5-dev
sudo apt-get install --force-yes pandoc

# scipy:
sudo apt-get install --force-yes gfortran
sudo apt-get install --force-yes libopenblas-dev
sudo apt-get install --force-yes liblapack-dev

#nlpserver
sudo apt-get install --force-yes libgflags-dev
sudo apt-get install --force-yes libgoogle-glog-dev

# MElt
# soon

## SERVER Configuration

# server configuration
sudo apt-get install --force-yes nginx

# UWSGI with pcre support
sudo apt-get install --force-yes libpcre3 libpcre3-dev
sudo apt-get install --force-yes python3-pip
#pip3 install --force-yes uwsgi

