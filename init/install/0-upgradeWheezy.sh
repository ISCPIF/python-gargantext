#!/bin/bash

sudo aptitude install postfix
# copy from tina
cp configurations/postfix/main.cf
sudo postfix reload

sed -i 's/wheezy/jessie/g' /etc/apt/sources.list
sudo aptitude update
sudo aptitude dist-upgrade


ssh-keygen

cat ~/.ssh/id_rsa.pub | mail alexandre@delanoe.org -s "Key Server $(hostname)"

echo "Put ~/.ssh/id_rsa.pub on remote to enable git pull please and press enter"
read answer

sudo mkdir /srv/gargantext
cd /srv

chown gargantua:www-data gargantext

git clone ssh orign ssh://gitolite@delanoe.org:1979/gargantext
