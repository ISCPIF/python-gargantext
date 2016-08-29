# About the DB settings during the tests

rloth 2016-08-22

#### Correct ordering strategies

Our specific database model causes a problem for the correct order of doing things

  - the good practice in creating the test framework is:
    1. create a child class of DiscoverRunner
    2. define a 'TEST' key in `settings.DATABASES.default`
    3. let the DiscoverRunner create the tables in his `__init__()` by calling `super.__init__()` from the child class  
     (cf. https://docs.djangoproject.com/en/1.10/topics/testing/advanced/)


  - but we have tables not in the migrations... so creating our full database model (with the `nodes_*` tables) implies either to hard-code their definitions or to:
     1. do a `django.setup()` first so we can load the SQLAlchemy models (`import gargantext.models`)
     2. from there use `util.db.Base` as the table definitions
      - Table('nodes', Column('id', Integer()...)
      - Table('ngrams' ...)
      - etc.
     3. Use those definitions to create the tables:  `table_definition.create(engine)`  
     *(cf. db_migrate.py)*



#### But we see these two ordering strategies are contradictory!

**Explanation**: Doing the `django.setup()` to get the models will load the app modules before using the test database created by `DiscoverRunner.__init__()`

**Consequence**: `util.db.session` will use the native settings for the "real DB" instead of the "test DB".



#### So we need to "cheat" a little bit...

**Solution 1**   *(=> will be better in the long run when the tables stop changing)*  
We could hard-code the list of tables and columns to create in the test DB. Then there would be no need to load the models to do the migration, so therefore no need to do a `django.setup()` before the `DiscoverRunner.__init__()`  


**Solution 2**  *(=> used now)*  
We do the `django.setup()` but we modify its `gargantext.settings.DATABASES` on-the-fly with this line:
```
DATABASES['default']['NAME'] = DATABASES['default']['TEST']['NAME']
```

This is a dirty hack because changing settings at runtime makes final values difficult to track, but this way, the setup part and the DiscoverRunner part will share the same DB name (`test_gargandb`)



### To inspect the testdb

Run tests with:
```
./manage.py test unittests/ --keepdb
```
And after the tests, connect to it as gargantua with `psql test_gargandb`
