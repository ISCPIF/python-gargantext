#!/usr/bin/bash
echo "Adding user gargantua";
sudo adduser --disabled-password --gecos "" gargantua;
echo "Creating the environnement into /srv/";
for dir in "/srv/gargantext" "/srv/gargantext_lib" "/srv/gargantext_static" "/srv/gargantext_media""/srv/env_3-5"; do
    sudo mkdir -p $dir ;
    sudo chown gargantua:gargantua $dir ;
done;
echo "Downloading the libs";
wget http://dl.gargantext.org/gargantext_lib.tar.bz2 \
&& tar xvjf gargantext_lib.tar.bz2 -o /srv/gargantext_lib \
&& sudo chown -R gargantua:gargantua /srv/gargantext_lib \
&& echo "Libs installed";
#cp ~/.ssh/id_rsa.pub id_rsa.pub
echo "Cloning the repo";
git clone ssh://gitolite@delanoe.org:1979/gargantext /srv/gargantext \
        && cd /srv/gargantext \
        && git fetch origin refactoring \
        && git checkout refactoring \
echo "Currently on /srv/gargantext refactoring branch";
