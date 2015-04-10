#!/bin/bash


cd /srv/
wget http://docs.delanoe.org/gargantext_lib.tar.bz2
sudo tar xvjf gargantext_lib.tar.bz2
sudo chown gargantua:gargantua /srv/gargantext_lib

cd /srv/gargantext_lib/js
git clone git@github.com:PkSM3/garg.git

# Installing TreeTagger

cp treetagger /srv/gargantext/parsing/Tagger/treetagger
cp nlpserver /srv/gargantext/parsing/Tagger/

# Installing nlpserver


