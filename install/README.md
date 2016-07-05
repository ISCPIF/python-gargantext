#Install Instructions for Gargantext (CNRS):

## Get the source code
by cloning gargantext into /srv/gargantext

``` bash
git clone ssh://gitolite@delanoe.org:1979/gargantext /srv/gargantext \
        && cd /srv/gargantext \
        && git fetch origin stable \
        && git checkout stable \
```


The folder will be /srv/gargantext:
* docs containes all informations on gargantext
    /srv/gargantext/docs/
* install contains all the installation files
    /srv/gargantext/install/

Help needed ?
See [http://gargantext.org/about](http://gargantext.org/about) and [tools](./contribution_guide.md) for the community

Two installation procedure are provided:

1. Semi-automatic installation  [EASY]
2. Step by step installation     [ADVANCED]

Here only semi-automatic installation is covered checkout [manual_install](manual_install.md)
to follow step by step procedure


##Prerequisites
## Init Setup
## Install
## Run

--------------------

# Semi automatic installation
All the procedure files are located into /srv/garantext/install/
``` bash
user@computer:$ cd /srv/garantext/install/
```

## Prerequisites

* A Debian based OS >= [FIXME]

* At least 35GO in /srv/ [FIXME]
    todo: reduce the size of gargantext lib
    todo: remove lib once docker is configured

! tip: if you have enought space for the full package you can:
        * resize your partition
        * make a simlink on gargantext_lib




##Init Setup
Prepare your environnement and make the initial setup.

This initial step creates a user for gargantext plateform along with dowloading additionnal libs and files.

It also install docker and build the docker image and build the gargantext box

``` bash
user@computer:/srv/garantext/install/$ .init.sh
```


### Install
Once the init step is done

* Enter into the docker environnement

Inside folder /srv/garantext/install/
enter the gargantext image
``` bash
user@computer:/srv/garantext/install/$ .docker/enterGargantextImage
```
go to the installation folder
``` bash
root@dockerimage8989809:$ cd /srv/gargantext/install/
```
    [ICI] Tester si les config de postgresql et python sont faits en amont à la création du docker file

* Install Python environment


``` bash
root@dockerimage8989809:/srv/garantext/install/$ python/configure
```
* Configure PostgreSql

Inside the docker image, execute as root:
``` bash
root@computer:/srv/garantext/install/$ postgres/configure
```
    [Si OK ] enlever ses lignes

Install Gargantext server

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



## Run Gargantext

Enter the docker container:
``` bash
/srv/gargantext/install/docker/enterGargantextImage
```
Inside the docker container:
``` bash
#start Database (postgresql)
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
Keep it open and  outside the docker launch browser

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


