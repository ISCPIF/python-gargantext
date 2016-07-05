#!/usr/bin/bash
echo "Adding user gargantua";
sudo adduser --disabled-password --gecos "" gargantua;
echo "Creating the environnement into /srv/";
for dir in "/srv/gargantext" "/srv/gargantext_lib" "/srv/gargantext_static" "/srv/gargantext_media""/srv/env_3-5"; do
    sudo mkdir -p $dir ;
    sudo chown gargantua:gargantua $dir ;
done;
echo "Downloading the libs. Please be patient!";
wget http://dl.gargantext.org/gargantext_lib.tar.bz2 \
&& tar xvjf gargantext_lib.tar.bz2 -o /srv/gargantext_lib \
&& sudo chown -R gargantua:gargantua /srv/gargantext_lib \
&& echo "Libs installed";
echo 'Install docker'
sudo apt-get install -y docker-engine
echo 'Build gargantext image'
cd /srv/gargantext/install/
./docker/config/build



#Next steps
#install and configure git
#sudo apt-get install -y git
#clone your SSH key
#cp ~/.ssh/id_rsa.pub id_rsa.pub
#clone the repo
#~ git clone ssh://gitolite@delanoe.org:1979/gargantext /srv/gargantext \
        #~ && cd /srv/gargantext \
        # get on branch
        #~ && git fetch origin unstable \
        #~ && git checkout unstable \
#~ echo "Currently on /srv/gargantext unstable branch";
#create your own branch
# git checkout -b my-unstable

