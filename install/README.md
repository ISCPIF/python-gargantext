#Gargantext
==========

<<<<<<< HEAD
Install Instructions for Gargantext (CNRS):

1. [SETUP](##SETUP)
2. [INSTALL](##INSTALL)
3. [RUN](##RUN)

## Help needed ?
See http://gargantext.org/about and tools for the community

## SETUP
Prepare your environnement

Create user gargantua

Main user of Gargantext is Gargantua (role of Pantagruel soon)!

``` bash
sudo adduser --disabled-password --gecos "" gargantua
```

Create the directories you need

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
├── gargantext_static
└── lost+found [error opening dir]

```

## Get the source code of Gargantext

Clone the repository of gargantext
``` bash
git clone ssh://gitolite@delanoe.org:1979/gargantext /srv/gargantext \
        && cd /srv/gargantext \
        && git fetch origin refactoring \
        && git checkout refactoring \
```

**Optionnal**: if you want to contribute clone the repo into your own branch

``` bash
git checkout -b username-refactoring refactoring
```

    ! TODO (soon) : git clone https://gogs.iscpif.fr/gargantext.git


## SETUP
Build your OS dependencies
2 ways, for each you need to install Debian GNU/Linux dependencies.

1. [EASY] [Docker way](#DOCKER)
2. [EXPERT] [Debian way](#DEBIAN)

### DOCKER
* Install docker
See [installation instruction for your distribution](https://docs.docker.com/engine/installation/)

#### Build your docker image
``` bash
cd /srv/gargantext/install/docker/dev
./build
```
You should see
```
Successfully built <container_id>
```

#### Enter into the docker environnement

``` bash
./srv/gargantext/install/docker/enterGargantextImage
```

#### Install Python environment
Inside the docker image, execute as root:
``` bash
/srv/gargantext/install/python/configure
```
#### Configure PostgreSql
Inside the docker image, execute as root:
``` bash
/srv/gargantext/install/postgres/configure
```
#### Exit the docker
``` exit
```
#### Get main librairies

Can be long, so be patient :)
``` bash
wget http://dl.gargantext.org/gargantext_lib.tar.bz2 \
&& tar xvjf gargantext_lib.tar.bz2 -o /srv/gargantext_lib \
&& sudo chown -R gargantua:gargantua /srv/gargantext_lib \
&& echo "Libs installed"
```

### DEBIAN
[EXPERTS] Debian way (directory install/debian)

## INSTALL Gargantext

### Enter docker container
``` bash
/srv/gargantext/install/docker/enterGargantextImage
```

### Inside docker container configure the database
``` bash
service postgresql start
su gargantua
source /srv/env_3-5/bin/activate
python /srv/gargantext/dbmigrate.py
/srv/gargantext/manage.py migrate
python /srv/gargantext/dbmigrate.py
python /srv/gargantext/dbmigrate.py
echo "TODO: Init first user"
```

FIXME: dbmigrate need to launched several times since tables are
ordered with alphabetical order (and not dependencies order)

### Inside docker container launch Gargantext
``` bash
service postgresql start
su gargantua
source /srv/env_3-5/bin/activate
/srv/gargantext/manage.py runserver 0.0.0.0:8000
python /srv/gargantext/init_accounts.py /srv/gargantext/install/init/account.csv
```

## RUN
### Outside docker container launch browser
``` bash
chromium http://127.0.0.1:8000/
```

Click on Test Gargantext
Login : gargantua
Password : autnagrag

Enjoy :)


=======
Install Instructions for Gargantext (CNRS).

## Help needed ?
See http://gargantext.org/about and tools for the community

## Create user Gargantua

Main user of Gargantext is Gargantua (role of Pantagruel soon)!
>>>>>>> constance-docker

``` bash
sudo adduser --disabled-password --gecos "" gargantua
```

<<<<<<< HEAD

=======
## Create the directories you need

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

## Get the source code of Gargantext

``` bash
git clone ssh://gitolite@delanoe.org:1979/gargantext /srv/gargantext \
        && cd /srv/gargantext \
        && git fetch origin refactoring \
        && git checkout refactoring \
```

### TODO (soon) : git clone https://gogs.iscpif.fr/gargantext.git

## Build your OS dependencies

2 ways, for each you need to install Debian GNU/Linux dependencies.

1) [EASY] Docker way (directory install/docker)
2) [EXPERTS] Debian way (directory install/debian)

## Build your docker image
``` bash
cd /srv/gargantext/install/docker/dev
./build
```

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
``` bash
wget http://dl.gargantext.org/gargantext_lib.tar.bz2 \
&& tar xvjf gargantext_lib.tar.bz2 -o /srv/gargantext_lib \
&& sudo chown -R gargantua:gargantua /srv/gargantext_lib \
&& echo "Libs installed"
```

## Configure && Launch Gargantext

### Enter docker container
``` bash
/srv/gargantext/install/docker/enterGargantextImage
```

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

### Inside docker container launch Gargantext
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
>>>>>>> constance-docker

