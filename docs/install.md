Install Instructions for Gargantext (CNRS):

Help needed ?
See [http://gargantext.org/about](http://gargantext.org/about) and [tools]() for the community


Prepare your environnement and make the initial installation.
Once you setup and install the Gargantext box. You can use ./install/run.sh utility
to load gargantext web plateform and access it throught your web browser

______________________________

1. [Prerequisites](##Prerequisites)

2. [SETUP](##Setup)

3. [INSTALL](##Install)

4. [RUN](##RUN)
______________________________
##Prerequisites

* A Debian based OS >= [FIXME]

* At least 35GO in the desired location of Gargantua [FIXME]
    todo: reduce the size of gargantext lib
    todo: remove lib once docker is configure

    tip: if you have enought space for the full package you can:
        * resize your partition
        * make a simlink on gargantext_lib

* A [docker engine installation](https://docs.docker.com/engine/installation/linux/)

##Setup
Prepare your environnement and make the initial setup.

Setup can be done in 2 ways:
    * [automatic setup](setup.sh) can be done by using the setup script provided [here](setup.sh)
    * [manual setup](manual_setup.md) if you want to change some parameters [here](manual_setup.md)

##Install

Two installation procedure are actually proposed:
* the docker way [easy]
* the debian way [advanced]

####DOCKER WAY [EASY]

* Install docker
See [installation instruction for your distribution](https://docs.docker.com/engine/installation/)

* Build your docker image

``` bash
cd /srv/gargantext/install/docker/config
./build
ID=$(docker build .) && docker run -i -t $ID
```

You should see

```
Successfully built <container_id>
```

* Enter into the docker environnement

``` bash
./srv/gargantext/install/docker/enterGargantextImage
```
    [ICI] Tester si les config de postgresql et python sont faits en amont à la création du docker file

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
#activate the virtualenv
source /srv/env_3-5/bin/activate
```
You have entered the virtualenv as shown with (env_3-5)
``` bash
(env_3-5) $ python /srv/gargantext/dbmigrate.py
(env_3-5) $  /srv/gargantext/manage.py makemigrations
(env_3-5) $  /srv/gargantext/manage.py migrate
(env_3-5) $  python /srv/gargantext/dbmigrate.py
#will create tables and not hyperdata_nodes
(env_3-5) $  python /srv/gargantext/dbmigrate.py
#will create table hyperdata_nodes
#launch first time the server to create first user
(env_3-5) $ /srv/gargantext/manage.py runserver 0.0.0.0:8000
(env_3-5) $  /srv/gargantext/init_accounts.py /srv/gargantext/install/init/account.csv
```

    FIXME: dbmigrate need to launched several times since tables are
    ordered with alphabetical order (and not dependencies order)
* Exit the docker
```
exit (or Ctrl+D)
```

####Debian way [advanced]

##Run Gargantext
* Launch Gargantext

Enter the docker container:
``` bash
/srv/gargantext/install/docker/enterGargantextImage
```
Inside the docker container:
``` bash
#start postgresql
service postgresql start
#change to user
su gargantua
#activate the virtualenv
source /srv/env_3-5/bin/activate
#go to gargantext srv
(env_3-5) $ cd /srv/gargantext/
#run the server
(env_3-5) $ /manage.py runserver 0.0.0.0:8000
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
See [User Guide](/demo/tuto.md) for quick usage example


