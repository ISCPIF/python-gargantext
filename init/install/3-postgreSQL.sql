In PostreSQL
-------------

1)  Ensure postgres is started: sudo /etc/init.d/postgresql start

2)  sudo su postgres

3)  psql

4)  CREATE USER gargantua WITH PASSWORD 'C8kdcUrAQy66U';
    (see gargantext_web/settings.py, DATABASES = { ... })
    
5)  CREATE DATABASE gargandb WITH OWNER gargantua;

6)  Ctrl + D

7)  psql gargandb

6)  CREATE EXTENSION hstore;

7)  Ctrl + D


