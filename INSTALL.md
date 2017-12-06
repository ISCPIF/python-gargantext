# Gargantext installation and dev environment

## TL;DR

You need `pipenv`, an up-to-date version of `pip`, and a PostgreSQL (>= 9.5)
database. To setup development environment and run test server:

    git clone -b gargantext-light ssh://git@gitlab.iscpif.fr:20022/humanities/gargantext.git gargantext-light
    cd gargantext-light
    make
    pipenv run ./manage runserver


## Requirements

### Up-to-date pip

On Debian-like distros, `pip` is not installed by default, if you didn't do it
already:

    sudo apt install python3-pip

Pipenv (see below) needs an up-to-date version of pip, on a Debian-like just
`apt upgrade`, otherwise upgrade it like so:

    pip install pip --user --upgrade

### Pipenv

You will need [pipenv][1] to easily get dependencies of Gargantext.
It handles packages and takes care of the virtualenv and environment variables.

There are various ways to install `pipenv`, see its [documentation][2] for more
insights. Here is the straightforward way:

    pip install pipenv --user

If you use `pipenv shell`, don't forget to leave the virtualenv (`exit` or
`<Ctrl-D>`) and enter it again each time you install or uninstall packages with
`pipenv` or `pip`, to avoid weird issues with your environment.

[1]: https://github.com/kennethreitz/pipenv
[2]: https://docs.pipenv.org/

## PostgreSQL

Gargantext rely on PostgreSQL (>= 9.5) for data persistence. To setup
database on a Debian-based OS:

    sudo apt-get install postgresql-9.6 postgresql-client-9.6
    sudo -u postgres psql -c "CREATE USER gargantua PASSWORD '<pass>' CREATEROLE BYPASSRLS"
    sudo -u postgres createdb -O gargantua gargandb


## Installation

To bootstrap Gargantext environment just cd into your local Gargantext repo and
do:

    make

Or for production (without dev dependencies and without DEBUG mode):

    make TARGET=prod

To specify a path for configuration file (by default gargantext.ini in current
directory), use GARGANTEXT_CONF environment variable. For example:

    GARGANTEXT_CONF=/etc/gargantext/gargantext.ini make TARGET=prod

You can specify path of PostgREST configuration the same way by setting
POSTGREST_CONF environment variable.

If everything is going well, you now have a clean virtualenv with every
packages you need to run Gargantext, and a fresh configuration file.

You can now run any command by prefixing it with `pipenv run` or by first
entering the virtualenv with `pipenv shell`. To run Gargantext django backend
test server you can do:

    pipenv run ./manage.py runserver


## Customize dev environment

To install specific packages without messing with dependencies, just use pip.
For example, to install ipython or bpython shells locally:

    pipenv run pip install ipython
    pipenv run pip install bpython
