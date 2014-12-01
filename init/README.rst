Install the requirements
------------------------

1)  Install all the Debian packages listed in dependances.deb
    (also: sudo apt-get install postgresql-contrib)

2)  Create a Pythton virtual enironnement

    On Debian:
    ---------
    sudo apt-get install python3.4-venv
    pyvenv3 /srv/gargantext_env

    On ubuntu:
    ---------
    sudo apt-get install python-pip
    sudo pip install -U pip
    sudo pip install -U virtualenv

    ensuite tu peux créer ton virtualenv dans le dossier de travail ou à un
    endroit choisi :

    virtualenv -p python3 /srv/gargantext_env

3)  Type: source [your virtual environment directory]/bin/activate

4)  Do your work!

5)  Type: deactivate


Configure stuff
---------------

1)  ln -s [the project folder] /srv/gargantext

2)  ln -s [your folder for tree tagger] [the project folder]/parsing/Tagger/treetagger

Warning: for ln, path has to be absolute!


In PostreSQL
-------------

1)  Ensure postgres is started: sudo /etc/init.d/postgresql start

2)  sudo su postgres

3)  psql

4)  CREATE USER alexandre WITH PASSWORD 'C8kdcUrAQy66U';
    (see gargantext_web/settings.py, DATABASES = { ... })
    
5)  CREATE DATABASE gargandb WITH OWNER alexandre;

6)  Ctrl + D

7)  psql gargandb

6)  CREATE EXTENSION hstore;

7)  Ctrl + D


Populate the database
---------------------

python manage.py syncdb


Start the Python Notebook server
--------------------------------

1)  In Pyvenv:
    python manage.py shell_plus --notebook

2)  Work from your browser!


Start the Django server
-----------------------

In Pyvenv:
python manage.py runserver
