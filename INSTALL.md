# Gargantext installation and dev environment

## Requirements

### Pipenv

You will need [pipenv][1] to easily get dependencies of Gargantext.
It handles packages and takes care of the virtualenv and environment variables.

There are various ways to install pipenv, see its [documentation][2] for more
insights. Here is the straightforward way:

    $ pip install --user pipenv

[1]: https://github.com/kennethreitz/pipenv
[2]: https://docs.pipenv.org/

## Installation

To bootstrap Gargantext environment just cd into your local Gargantext repo and
do:

    $ pipenv install

If everything is going well, you now have a clean virtualenv with every
packages you need to run Gargantext. Here is how to get the path of the
virtualenv directory pipenv just created:

    $ pipenv --venv

You can now run any command by prefixing it with `pipenv run` or by first
entering the virtualenv with `pipenv shell`. To run Gargantext django backend
test server you can do:

    $ pipenv run ./manage.py runserver

But also:

    $ pipenv shell
    $ ./manage.py runserver
    $ ... continue in your virtualenv ...

## Customize dev environment

To install specific packages without messing with dependencies, just use pip.
For example, to install ipython or bpython shells:

    $ pip install ipython
    $ pip install bpython
