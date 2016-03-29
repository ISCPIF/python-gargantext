#!/bin/bash

#MAINTAINER ISCPIF <alexandre.delanoe@iscpif.fr>

git clone ssh://gitolite@delanoe.org:1979/gargantext /srv/gargantext \
	&& cd /srv/gargantext \
	&& git fetch origin refactoring-alex \
	&& git checkout refactoring-alex

cd /srv/gargantext/install \
   && /usr/bin/virtualenv --py=/usr/bin/python3.5 /srv/env_3-5 \
   && /bin/bash -c 'source /srv/env_3-5/bin/activate' \
   && /bin/bash -c '/srv/env_3-5/bin/pip install git+https://github.com/zzzeek/sqlalchemy.git@rel_1_1' \
   && /bin/bash -c '/srv/env_3-5/bin/pip install -r /srv/gargantext/install/python/requirements.txt' \


## INSTALL MAIN DEPENDENCIES

cd /tmp && wget http://dl.gargantext.org/gargantext_lib.tar.bz2 \
     && tar xvjf gargantext_lib.tar.bz2 -o /srv/gargantext_lib \
     && chown -R gargantua:gargantua /srv/gargantext_lib

## End of configuration
## be sure that postgres is running
cd /srv/gargantext && /bin/bash -c 'source /srv/bin/env_3-5/bin/activate' \
    && /srv/gargantext/manage.py shell < /srv/gargantext/init.py


echo "Gargantua: END of the installation of Gargantext"

