Install the requirements
------------------------

1)  Install all the Debian packages listed in dependances.deb
    (also: sudo apt-get install postgresql-contrib)

2)  Create a Python virtual enironnement

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

    sudo virtualenv -p python3 /srv/gargantext_env

3)  Type: source [your virtual environment directory]/bin/activate

4)  sudo chown -R user:user /srv/gargantext_env
    pip install -r /srv/gargantext/init/install/2-requirements.txt

5)  Type: deactivate


In PostreSQL version 9.4 needed
-------------------------------

1)  Ensure postgres is started: sudo /etc/init.d/postgresql start

2)  sudo su postgres

3)  psql

4)  CREATE USER gargantua WITH PASSWORD 'C8kdcUrAQy66U';
    (see gargantext_web/settings.py, DATABASES = { ... })
    
5)  CREATE DATABASE gargandb WITH OWNER gargantua;

6)  Ctrl + D

7)  psql gargandb

8)  Ctrl + D



Populate the database
---------------------

python manage.py syncdb

run as postgres or gargantua user:
psql -d gargandb -f /srv/gargantext/init/sql/changeDateformat.sql

Last steps of configuration
---------------------------

1)  If your project is not in /srv/gargantext:
    ln -s [the project folder] /srv/gargantext

2)  Install de Libraries
    cd /srv
    wget http://dl.gargantext.org/gargantext_lib.tar.bz2
    tar xvjf gargantext_lib.tar.bz2
    rm gargantext_lib.tar.bz2

3)  init nodetypes and main variables
    /srv/gargantext/manage.py shell < /srv/gargantext/init.py

4)  patch CTE:
    patch /srv/gargantext_env/lib/python3.4/site-packages/cte_tree/models.py /srv/gargantext/init/patches/cte_tree.models.diff

5)  DO NOT use the default aldjemy package:
    cd /tmp
    git clone https://github.com/mathieurodic/aldjemy
    cd aldjemy
    python3 setup.py install



Start Turbo parser server
-------------------------
See dependences in init/dependences.sh
See README for install instructions /srv/gargantext/parsing/Taggers/lib/nlpserver/README.rst


Start the Python Notebook server
--------------------------------
1)  In Pyvenv:
    python manage.py shell_plus --notebook

2)  Work from your browser!


Start the Django server
-----------------------
in bash to launch python env : /srv/gargantext_env/bin/activate
In Pyvenv:
$ python manage.py runserver


For Production Server
---------------------
git checkout stable

$ sudo aptitude install rabbitmq-server
$ sudo aptitude install tmux
# In your python envrionment:
$ tmux -c ./manage.py celery worker --loglevel=info
$ python manage.py runserver

Versions on git
---------------

stable branch    : current version  for production server with nginx config (and tina branch for tina/apache server)
testing branch   : current version for users' tests
unstable branch  : current version for developers

