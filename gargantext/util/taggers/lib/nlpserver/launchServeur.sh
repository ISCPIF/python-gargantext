#!/bin/bash
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/srv/gargantext_lib/taggers/nlpserver:/srv/gargantext_lib/taggers/nlpserver/TurboParser/deps/local/lib:"

if [[ ! "$VIRTUAL_ENV" ]]
then
  source /srv/env_3-5/bin/activate
fi

python3 /srv/gargantext/gargantext/util/taggers/lib/nlpserver/server.py
