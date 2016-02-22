# Installation

```bash
sudo apt-get install python3.4
sudo pip3 install virtualenv
sudo apt-get install rabbitmq-server
virtualenv-3.4 VENV
source VENV/bin/activate
pip install git+https://github.com/zzzeek/sqlalchemy.git@rel_1_1
pip install -U -r requirements.txt
```


# Migrate database

## Django models

```bash
./manage.py makemigrations
./manage.py migrate --fake-initial
```

...or if it fails, try the commandes below:

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
manage.py celeryd --loglevel=INFO # to ensure Celery is properly started
manage.py runserver
```
