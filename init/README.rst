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

    sudo virtualenv -p python3 /srv/gargantext_env

3)  Type: source [your virtual environment directory]/bin/activate

4)  sudo chown -R user:user /srv/gargantext_env
    pip install -r /srv/gargantext/init/requirements.txt

5)  Type: deactivate


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


Last steps of configuration
---------------------------

1)  If your project is not in /srv/gargantext:
    ln -s [the project folder] /srv/gargantext

2)  build gargantext_lib:
    cd /srv/
    wget http://docs.delanoe.org/gargantext_lib.tar.bz2
    sudo tar xvjf gargantext_lib.tar.bz2
    sudo chown user:user /srv/gargantext_lib

3)  Explorer: 
    cd /srv/gargantext_lib/js
    git clone git@github.com:PkSM3/garg.git

4)  Adapt all symlinks:
    ln -s [your folder for tree tagger] [the project folder]/parsing/Tagger/treetagger
    Warning: for ln, path has to be absolute!

5)  patch CTE:
    patch /srv/gargantext_env/lib/python3.4/site-packages/cte_tree/models.py /srv/gargantext/init/cte_tree.models.diff

6)  init nodetypes and main variables
    /srv/gargantext/manage.py shell < /srv/gargantext/init/init.py

7)  DO NOT use the default aldjemy package:
    cd /tmp
    git clone https://github.com/mathieurodic/aldjemy
    cd aldjemy
    python3 setup.py install


Extras
=======

Last steps of configuration:
----------------------------

1) If your project is not in /srv/gargantext:
    ln -s [the project folder] /srv/gargantext

2) build gargantext_lib
    wget http://docs.delanoe.org/gargantext_lib.tar.bz2
    cd /srv/
    sudo tar xvjf gargantext_lib.tar.bz2
    sudo chown user:user /srv/gargantext_lib

3) Explorer:

create mkdir /srv/gargantext_lib/js
sudo chown -R user:user /srv/gargantext_lib/

cd /srv/gargantext_lib/js
git clone git@github.com:PkSM3/garg.git

4)  Adapt all symlinks:
ln -s [your folder for tree tagger] [the project folder]/parsing/Tagger/treetagger
Warning: for ln, path has to be absolute!

5) patch CTE
patch /srv/gargantext_env/lib/python3.4/site-packages/cte_tree/models.py /srv/gargantext/init/cte_tree.models.diff

6) init nodetypes and main variables
/srv/gargantext/manage.py shell < /srv/gargantext/init/init.py


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

