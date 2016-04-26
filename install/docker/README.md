Docker installation

## Quick Manual
## Install docker.io && sudo
## sudo docker build -t gargantext .
## docker run -i -t gargantext /bin/bash

# Install Docker
# Debian/Ubuntu: apt-get install docker

# run turboparser port, with python 3.4
#docker run -d -p 8000:8000 -v /srv:/srv -t gargantext python /srv/gargantext/gargantext.py


For dev: cd dev and run install
Fro prod : install dev-version, cd prod and run install
