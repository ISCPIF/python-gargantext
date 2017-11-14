# Gargantext installation and dev environment

## TL;DR

You need `pipenv` and an up-to-date version of `pip`. To setup development
environment and run test server:

    $ make dev
    $ pipenv run ./manage runserver


## Requirements

### Up-to-date pip

On Debian-like distros, `pip` is not installed by default, if you didn't do it
already:

    $ sudo apt install python3-pip

Pipenv (see below) needs an up-to-date version of pip, on a Debian-like just
`apt upgrade`, otherwise upgrade it like so:

    $ pip install pip --user --upgrade

### Pipenv

You will need [pipenv][1] to easily get dependencies of Gargantext.
It handles packages and takes care of the virtualenv and environment variables.

There are various ways to install `pipenv`, see its [documentation][2] for more
insights. Here is the straightforward way:

    $ pip install pipenv --user

If you use `pipenv shell`, don't forget to leave the virtualenv (`exit` or
`<Ctrl-D>`) and enter it again each time you install or uninstall packages with
`pipenv` or `pip`, to avoid weird issues with your environment.

[1]: https://github.com/kennethreitz/pipenv
[2]: https://docs.pipenv.org/


## Installation

To bootstrap Gargantext environment just cd into your local Gargantext repo and
do:

    $ make dev

If everything is going well, you now have a clean virtualenv with every
packages you need to run Gargantext.

You can now run any command by prefixing it with `pipenv run` or by first
entering the virtualenv with `pipenv shell`. To run Gargantext django backend
test server you can do:

    $ pipenv run ./manage.py runserver


## Customize dev environment

To install specific packages without messing with dependencies, just use pip.
For example, to install ipython or bpython shells locally:

    $ pipenv run pip install ipython
    $ pipenv run pip install bpython
