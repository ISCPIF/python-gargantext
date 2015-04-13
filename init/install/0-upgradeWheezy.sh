#!/bin/bash

apt-get install sudo

sudo apt-get install postfix
# copy from tina
sudo cp 0*cf /etc/postfix/main.cf
sudo postfix reload

sed -i 's/wheezy/jessie/g' /etc/apt/sources.list
sudo aptitude update
sudo aptitude dist-upgrade

# dpkg-reconfigure locales => add GB

ssh-keygen

cat ~/.ssh/id_rsa.pub | mail alexandre@delanoe.org -s "Key Server $(hostname)"

echo "Put ~/.ssh/id_rsa.pub on remote to enable git pull please and press enter"
read answer

sudo mkdir /srv/gargantext
cd /srv

chown gargantua:www-data gargantext

git clone ssh orign ssh://gitolite@delanoe.org:1979/gargantext
