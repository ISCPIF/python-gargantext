#!/bin/bash

sudo docker export $(sudo docker ps -l | awk '{print $1}' | grep -v CONTAINER | head -n 1) > /tmp/gargantext_docker_image.tar

# To import the docker
#sudo docker import - gargantext:latest < data.tar
#sudo cat data.tar | docker import - gargantext

