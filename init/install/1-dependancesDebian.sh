#!/bin/dash

# TODO do sudo apt-get install --force-yes 


sudo apt-get install postgresql
sudo apt-get install postgresql-contrib
sudo apt-get install rabbitmq-server
sudo apt-get install tmux

sudo apt-get install python3.4-venv
#sudo apt-get install python-virtualenv

sudo apt-get install libpng12-dev
sudo apt-get install libpng-dev
sudo apt-get install libfreetype6-dev
sudo apt-get install python-dev
sudo apt-get install libpq-dev
sudo apt-get install libpq-dev

sudo apt-get build-dep python-matplotlib
sudo apt-get install python-matplotlib

#Paquets Debian a installer
# easy_install -U distribute (matplotlib)
#lxml
sudo apt-get install libffi-dev
sudo apt-get install libxml2-dev
sudo apt-get install libxslt1-dev

# ipython readline
sudo apt-get install libncurses5-dev
sudo apt-get install pandoc

# scipy:
sudo apt-get install gfortran
sudo apt-get install libopenblas-dev
sudo apt-get install liblapack-dev

#nlpserver
sudo apt-get install libgflags-dev
sudo aptitude install libgoogle-glog-dev

# MElt
# soon

## SERVER Configuration

# server configuration
sudo apt-get install nginx

# UWSGI with pcre support
sudo apt-get install libpcre3 libpcre3-dev
sudo apt-get install python3-pip
pip3 install uwsgi

