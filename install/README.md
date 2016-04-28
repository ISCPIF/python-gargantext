Gargantext
==========

Install Instructions for Gargantext (CNRS).

1. [SETUP](##SETUP)
2. [INSTALL](##INSTALL)
3. [RUN](##RUN)

## Support needed ?
See http://gargantext.org/about and tools for the community

## Setup
Prepare your environnement

Build your OS dependencies inside a docker


``` bash
cd /srv/gargantext/install/docker/dev
./build
```

## INSTALL

### Enter docker container
``` bash
/srv/gargantext/install/docker/enterGargantextImage
```

### Create the directories you need

``` bash
for dir in "/srv/gargantext"
           "/srv/gargantext_lib"
           "/srv/gargantext_static"
           "/srv/gargantext_media"
           "/srv/env_3-5"; do 
    sudo mkdir -p $dir ;
    sudo chown gargantua:gargantua $dir ; 
done
```

You should see:

```bash
$tree /srv
/srv
├── gargantext
├── gargantext_lib
├── gargantext_media
│   └── srv
│       └── env_3-5
└── gargantext_static

```

## Get the source code of Gargantext


```bash
cp ~/.ssh/id_rsa.pub id_rsa.pub
`
git clone ssh://gitolite@delanoe.org:1979/gargantext /srv/gargantext \
        && cd /srv/gargantext \
        && git fetch origin refactoring \
        && git checkout refactoring \
```

TODO (soon) : git clone https://gogs.iscpif.fr/gargantext.git


## Install Python environment
Inside the docker image, execute as root:
``` bash
/srv/gargantext/install/python/configure
```

## Configure PostgreSql
Inside the docker image, execute as root:
``` bash
/srv/gargantext/install/postgres/configure
```

## Get main librairies

Can be long, so be patient :)
``` bash
wget http://dl.gargantext.org/gargantext_lib.tar.bz2 \
&& sudo tar xvjf gargantext_lib.tar.bz2 --directory /srv/gargantext_lib \
&& sudo chown -R gargantua:gargantua /srv/gargantext_lib \
&& echo "Libs installed"
```

## Configure && Launch Gargantext

### Inside docker container configure the database
``` bash
service postgresql start
su gargantua
source /srv/env_3-5/bin/activate
python /srv/gargantext/dbmigrate.py
/srv/gargantext/manage.py migrate
python /srv/gargantext/dbmigrate.py
python /srv/gargantext/dbmigrate.py
python /srv/gargantext/init_accounts.py /srv/gargantext/install/init/account.csv
```

FIXME: dbmigrate need to launched several times since tables are
ordered with alphabetical order (and not dependencies order)

## RUN

Inside docker container launch Gargantext
``` bash
service postgresql start
su gargantua
source /srv/env_3-5/bin/activate
/srv/gargantext/manage.py runserver 0.0.0.0:8000
```

### Outside docker container launch browser
``` bash
chromium http://127.0.0.1:8000/
```

Click on Test Gargantext
Login : gargantua
Password : autnagrag

Enjoy :)

