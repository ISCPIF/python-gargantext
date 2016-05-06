Gargantext
===========

Install Instructions for Gargantext (CNRS):

=> Help needed ?
See [http://gargantext.org/about](http://gargantext.org/about) and [tools]() for the community

1. [SETUP](##SETUP)
2. [INSTALL](##INSTALL)
*.1 with [docker](####DOCKER) [EASY]
*.2 with [debian](####DEBIAN) [EXPERT]

3. [RUN](##RUN)


##SETUP
Prepare your environnement

* Create user gargantua
Main user of Gargantext is Gargantua (role of Pantagruel soon)!

``` bash
sudo adduser --disabled-password --gecos "" gargantua
```

* Create the directories you need

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
* Get the main libraries

``` bash
wget http://dl.gargantext.org/gargantext_lib.tar.bz2 \
&& tar xvjf gargantext_lib.tar.bz2 -o /srv/gargantext_lib \
&& sudo chown -R gargantua:gargantua /srv/gargantext_lib \
&& echo "Libs installed"
```

* Get the source code of Gargantext

by cloning the repository of gargantext
``` bash
git clone ssh://gitolite@delanoe.org:1979/gargantext /srv/gargantext \
        && cd /srv/gargantext \
        && git fetch origin refactoring \
        && git checkout refactoring \
```

    TODO(soon): git clone https://gogs.iscpif.fr/gargantext.git
    TODO(soon): install/setup.sh

* **Optionnal**: if you want to contribute clone the repo into your own branch

``` bash
git checkout -b username-refactoring refactoring
```


##INSTALL
Build your OS dependencies
2 ways, for each you need to install Debian GNU/Linux dependencies.

####DOCKER WAY [EASY]

* Install docker
See [installation instruction for your distribution](https://docs.docker.com/engine/installation/)

* Build your docker image

``` bash
cd /srv/gargantext/install/docker/dev
./build
```

You should see

```
Successfully built <container_id>
```

* Enter into the docker environnement

``` bash
./srv/gargantext/install/docker/enterGargantextImage
```

* Install Python environment

Inside the docker image, execute as root:
``` bash
/srv/gargantext/install/python/configure
```
* Configure PostgreSql

Inside the docker image, execute as root:
``` bash
/srv/gargantext/install/postgres/configure
```
* Exit the docker
```
exit (or Ctrl+D)
```


####DEBIAN way [EXPERT]

[EXPERTS] Debian way (directory install/debian)



Install Gargantext server

* Enter docker container
``` bash
/srv/gargantext/install/docker/enterGargantextImage
```

*  Configure the database
Inside the docker container:
``` bash
service postgresql start
#su gargantua
source /srv/env_3-5/bin/activate
python /srv/gargantext/dbmigrate.py
/srv/gargantext/manage.py makemigrations
/srv/gargantext/manage.py migrate
python /srv/gargantext/dbmigrate.py
#will create tables and not hyperdata_nodes
python /srv/gargantext/dbmigrate.py
#will create table hyperdata_nodes
#launch first time the server to create first user
/srv/gargantext/manage.py runserver 0.0.0.0:8000
/srv/gargantext/init_accounts.py /srv/gargantext/install/init/account.csv
```

    FIXME: dbmigrate need to launched several times since tables are
    ordered with alphabetical order (and not dependencies order)

##RUN
* Launch Gargantext

Inside the docker container:
``` bash
#start postgresql
service postgresql start
#change to user
su gargantua
#activate the virtualenv
source /srv/env_3-5/bin/activate
#go to gargantext srv
cd /srv/gargantext/
#run the server
/manage.py runserver 0.0.0.0:8000
```


* Launch browser
outside the docker

``` bash
chromium http://127.0.0.1:8000/
```
* Click on Test Gargantext
```
Login : gargantua
Password : autnagrag
```
Enjoy :)
See [User Guide](./tuto.md) for quick usage example


