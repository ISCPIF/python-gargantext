#!/bin/bash


export LD_LIBRARY_PATH=":/srv/gargantext_lib/taggers/nlpserver/TurboParser/deps/local/lib:"

source /srv/env_3-5/bin/activate

python server.py

