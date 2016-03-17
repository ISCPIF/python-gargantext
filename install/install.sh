#/bin/bash

# Install Docker
# Debian/Ubuntu: apt-get install docker

# run turboparser port, with python 3.4
#docker run -d -p 8000:8000 -v /srv:/srv -t gargantext python /srv/gargantext/gargantext.py


# launch 
#cd /srv/gargantext

#source /srv/env_3-5/bin/activate && 
#docker run -d -p 8000:8000 -v /srv:/srv -t gargantext python /srv/gargantext/gargantext.py

docker build -t gargantext .

