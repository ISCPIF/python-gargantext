# Gargantext backend configuration and installation

## TL;DR

Gargantext main backend is written in Python 3.5. For a basic setup you need
an up-to-date version of `pip`, `pipenv`, a PostgreSQL (>= 9.5) database,
RabbitMQ (default message broker for asynchronous tasks) and
[PostgREST](https://postgrest.com/). See below for more details.

To setup a development environment and run backend servers in DEBUG mode:

    git clone -b gargantext-light ssh://git@gitlab.iscpif.fr:20022/humanities/gargantext.git gargantext-light
    cd gargantext-light
    make setup
    pipenv run make start

By default Django test server is running at <http://localhost:8000>, and
PostgREST at <http://localhost:3000>.

Web server `uWSGI` is needed for production, behind any good enough HTTP
server, for example `nginx`.


## Requirements

External dependencies are listed below. Python ones are automatically handled
by `pipenv` and are mainly Django, Celery, SQLAlchemy and Alembic. See
`./Pipfile` for details about used versions.

### Up-to-date pip

On Debian-like distros, `pip` is not installed by default, if you didn't do it
already:

    sudo apt-get install python3-pip

Pipenv (see below) needs an up-to-date version of pip, on a Debian-like just
`apt-get upgrade`, otherwise upgrade it like so:

    pip install pip --user --upgrade

### Pipenv

You will need [pipenv][1] to easily get dependencies of Gargantext. It handles
python packages and takes care of the virtualenv and environment variables.

There are various ways to install `pipenv`, see its [documentation][2] for more
insights. Here is the straightforward way:

    pip install pipenv --user --upgrade

[1]: https://github.com/kennethreitz/pipenv
[2]: https://docs.pipenv.org/

### PostgreSQL

Gargantext rely on [PostgreSQL](https://www.postgresql.org/) (>= 9.5) for data
persistence. To install it on a Debian-based OS:

    sudo apt-get install postgresql-9.6 postgresql-client-9.6

To setup Gargantext database:

    sudo -u postgres psql -c "CREATE USER gargantua PASSWORD '<pass>' CREATEROLE BYPASSRLS"
    sudo -u postgres createdb -O gargantua gargandb

### Celery

[Celery](http://www.celeryproject.org/) is used to handle asynchronous tasks,
its installation is handled by `pipenv` so you don't need to take care of it,
just note that version 3.1 is used because `djcelery` is used for django admin
integration.

Celery 3.1 documentation: <http://docs.celeryproject.org/en/3.1/>

### RabbitMQ

[RabbitMQ](http://www.rabbitmq.com/) is the default[^2] message broker of
Celery, version 3.6 is enough. Installations instructions here:
<https://www.rabbitmq.com/download.html>.

To install it on Debian:

    sudo apt-get install rabbitmq-server

[^2]: It it is possible to use another broker, but RabbitMQ is the only one
supported out of the box, plus it is really simple to deploy. See
<http://docs.celeryproject.org/en/latest/getting-started/brokers/index.html>.

### PostgREST

See <https://postgrest.com/en/v4.1/tutorials/tut0.html#step-3-install-postgrest>
for installation instructions.

### uWSGI

[uWSGI](https://uwsgi-docs.readthedocs.io/en/latest/) is the web server used by
Gargantext in production. It is supposed to run behind an HTTP server such as
nginx.

To install it on Debian:

    sudo apt-get install uwsgi


## Installation

To bootstrap Gargantext environment just cd into your local Gargantext repo and
do:

    make setup

Or for production (without dev dependencies and without `DEBUG` mode):

    make ENVIR=prod setup

If you want to specify custom paths for configuration files (by default
`gargantext.ini` and `postgrest.conf` in current directory), use
`GARGANTEXT_CONF` and `POSTGREST_CONF` environment variable. For example:

    GARGANTEXT_CONF=/etc/gargantext/gargantext.ini \
    POSTGREST_CONF=/etc/gargantext/postgrest.conf make ENVIR=prod setup

If everything is going well, you now have a clean virtualenv with every
packages you need to run Gargantext, and fresh configuration files.

You can now run any command by prefixing it with `pipenv run` or by first
entering the virtualenv with `pipenv shell`. If you use `pipenv shell`, don't
forget to leave the virtualenv (`exit` or `<Ctrl-D>`) and enter it again each
time you install or uninstall packages with `pipenv` or `pip`, to avoid weird
issues with your environment.

To run Gargantext backend servers do:

    pipenv run make start

If you want to run production servers in a development environment (or dev
servers in prod) just specify environment like this:

    # Run production servers regardless of current environment
    pipenv run make ENVIR=prod start
    # Don't forget to also set ENVIR at shutdown
    pipenv run make ENVIR=prod stop


## Configuration

Configuration is located in three files: `.env` (environment variables),
`gargantext.ini` and `postgrest.conf` (these file names are default values,
they can be specified in `GARGANTEXT_CONF` and `POSTGREST_CONF` env variables).

These files are automatically generated by running `make setup` (or
`make ENVIR=prod setup`), which takes care of the tedious work.

To generate configuration again, one can run `./tools/mkconf.sh -f <target>`
where `<target>` can be `dev` or `prod`. Be careful, this script will change
Django secret key and PostgREST role password, so all current tokens and
sessions will be invalidated.

### Environment variables

Configured in `.env` (loaded by `pipenv` when running `pipenv run` or
`pipenv shell`).

* `DJANGO_SETTINGS_MODULE`: python file path of the django settings module
* `GARGANTEXT_CONF`: django backend and uwsgi configuration file path
* `POSTGREST_CONF`: postgrest configuration file path

### Django backend

Configured in `GARGANTEXT_CONF` (`gargantext.ini` by default) under `[django]`
section. You can override options listed below with environment variables. For
example, to start production servers with DEBUG mode disabled from a
development environment, you can do: `DEBUG=False make ENVIR=prod start`.

See `settings.py` (full path in `DJANGO_SETTINGS_MODULE`) to understand details
about how these options are used.

* `DEBUG`: `True` | `False`
* `SECRET_KEY`: arbitrary string used by django in various ways[^1], and to
  generate JSON Web Tokens, so it MUST be reflected in PostgREST configuration
* `ALLOWED_HOSTS`: space separated list of allowed hosts
* `TIME_ZONE`: see <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>
* `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASS`: database settings
* `LOG_FILE`: django backend log file path
* `LOG_LEVEL`: `DEBUG` | `INFO` | `WARNING` | `ERROR` | `CRITICAL`
* `LOG_FORMATTER`: `simple` | `verbose`, formatters can be added in settings.py
* `TESTSERVER_PIDFILE`: pidfile for the testserver (only used by startup script)
* `CELERYD_PID_FILE`: pidfile for celery main worker
* `CELERYD_LOG_FILE`: celery log file path
* `CELERYD_LOG_LEVEL`: `DEBUG` | `INFO` | `WARNING` | `ERROR` | `CRITICAL`

[^1]: Details here: <https://stackoverflow.com/questions/15170637/effects-of-changing-djangos-secret-key#answer-15383766>.

### uWSGI

Configured in `GARGANTEXT_CONF` (`gargantext.ini` by default) under `[uwsgi]`
section.

uWSGI (used to serve django backend in production) configuration is not very
well documented. Here is a comprehensive but very harsh reference of all its
options: <https://uwsgi-docs.readthedocs.io/en/latest/Options.html>.

Here are some general options you may need to change:

* `daemonize`: log file path
* `log-reopen`: a `true` value tells uWSGI to write a new file each day
* `pidfile`: pidfile of master process

### PostgREST

Configured in `POSTGREST_CONF` (`postgrest.conf` by default).

Here are Gargantext specific options used by our startup script (NB: these
options won't be taken into account by postgrest itself):

* `pidfile`: pidfile of postgrest process
* `logfile`: log file path

For general options, see <https://postgrest.com/en/v4.3/install.html#configuration>.


## Development

### Customize dev environment

To install specific packages without messing with dependencies, just use pip.
For example, to install ipython or bpython shells locally:

    pipenv run pip install ipython
    pipenv run pip install bpython

### Pylint

> Pylint is a tool that checks for errors in Python code, tries to enforce a
> coding standard and looks for code smells.

See `pylintrc` for configuration. Be aware that pylint is slow to do its work,
just be patient.

To check for errors:

    pipenv run pylint gargantext

To get a full report with a dependency graph:

    pipenv run pylint -r y gargantext
    # To review a particular module pass its folder to pylint:
    pipenv run pylint -r y gargantext/backend
