#!/bin/bash


cd /tmp/
wget http://docs.delanoe.org/gargantext_lib.tar.bz2
cd /srv/
sudo mkdir gargantext_lib
sudo chown -R gargantua:www-data /srv/gargantext_lib

tar xvjf /tmp/gargantext_lib.tar.bz2
sudo chown -R gargantua:www-data /srv/gargantext_lib

cd /srv/gargantext_lib/js
git clone git@github.com:PkSM3/garg.git

