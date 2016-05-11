# Gargantext Installation

You will find here a Dockerfile and docker-compose script 
that builds a development container for Gargantex
along with a PostgreSQL 9.5.X server.

*  Install Docker
On your host machine, you need Docker.
[Installation guide details](https://docs.docker.com/engine/installation/#installation)

* clone the gargantex repository and get the refactoring branch
```
git clone ssh://gitolite@delanoe.org:1979/gargantext /srv/gargantext
cd /srv/gargantext
git fetch origin refactoring
git checkout refactoring
Install additionnal dependencies into gargantex_lib
```
wget http://dl.gargantext.org/gargantext_lib.tar.bz2 \
     && sudo tar xvjf gargantext_lib.tar.bz2 -o /srv/gargantext_lib \
     && sudo chown -R gargantua:gargantua /srv/gargantext_lib \
```

* Developers: create your own branch based on refactoring 

see [CHANGELOG](CHANGELOG.md) for migrations and branches name

```
git checkout-b username-refactoring refactoring

```
Build the docker images: 
- a database container
- a gargantext container

```
cd /srv/gargantext/install/
docker-compose build -t gargantex /srv/gargantext/install/docker/config/
docker-compose run web bundle install
```
Finally, setup the PostgreSQL database with the following commands.
```
docker-compose run web bundle exec rake db:create
docker-compose run web bundle exec rake db:migrate
docker-compose run web bundle exec rake db:seed
```

## OS

## Debian Stretch
See install/debian

If you do not have a Debian environment, then install docker and 
execute /srv/gargantext/install/docker/dev/install.sh

You need a docker image.
All the steps are explained in [docker/dev/install.sh](docker/dev/install.sh) (not automatic yet).

Bug reports are welcome.


