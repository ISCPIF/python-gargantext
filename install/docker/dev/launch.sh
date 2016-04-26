#!/bin/bash


sudo docker run -i -p 8000:8000 \
                   -v /srv:/srv \
                   -v /home/alexandre:/home/alexandre \
                   -t gargantext:latest \
                   /bin/bash

#sudo docker run -i --name srv -v /srv:/srv -t gargantext:latest /bin/bash
