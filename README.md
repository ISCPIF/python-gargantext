# Installation

First, install Python 3.5 (see https://www.python.org/downloads/ for
download links).

```bash
cd /tmp
wget https://www.python.org/ftp/python/3.5.1/Python-3.5.1.tar.xz
tar xvfJ Python-3.5.1.tar.xz
cd Python-3.5.1
./configure
make -j4 # option is for multithreading
sudo make install
```

Other components are required:

```bash
sudo pip3.5 install virtualenv
sudo apt-get install rabbitmq-server
```

Then build a virtual environment:

```bash
virtualenv-3.5 VENV
source VENV/bin/activate
pip3.5 install git+https://github.com/zzzeek/sqlalchemy.git@rel_1_1
pip3.5 install -U -r requirements.txt
```


# Migrate database

## Django models

```bash
./manage.py makemigrations
./manage.py migrate --fake-initial
```

...or...

```bash
./manage.py makemigrations
./manage.py migrate --run-syncdb
```

(see [Django documentation](https://docs.djangoproject.com/en/1.9/topics/migrations/))

## SQLAlchemy models

```bash
./dbmigrate.py
```


# Start the Django server

```bash
./manage.py celeryd --loglevel=INFO # to ensure Celery is properly started
./manage.py runserver
```
