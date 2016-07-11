"""
A test runner derived from default (DiscoverRunner) but adapted to our custom DB

cf. docs.djangoproject.com/en/1.9/topics/testing/advanced/#using-different-testing-frameworks
cf. gargantext/settings.py => TEST_RUNNER
cf. dbmigrate.py
"""

# basic elements
from django.test.runner  import DiscoverRunner, get_unique_databases_and_mirrors
from sqlalchemy          import create_engine
from gargantext.settings import DATABASES

# things needed to create a user
from django.contrib.auth.models import User

# here we setup a minimal django so as to load SQLAlchemy models ---------------
# and then be able to import models and Base.metadata.tables
from os import environ
from django import setup
environ.setdefault("DJANGO_SETTINGS_MODULE", "gargantext.settings")
setup()   # models can now be imported
from gargantext import models # Base is now filled
from gargantext.util.db  import Base  # cf. Base.metadata.tables

# things needed to provide a session
from sqlalchemy.orm import sessionmaker, scoped_session

# ------------------------------------------------------------------------------

class GargTestRunner(DiscoverRunner):
    """
    We use the default test runner but we just add
    our own dbmigrate elements at db creation

    => we let django.test.runner do the test db creation + auto migrations
    => we retrieve the test db name from django.test.runner
    => we create a test engine like in gargantext.db.create_engine but with the test db name
    => we create tables for our models like in dbmigrate with the test engine

    TODO: list of tables to be created are hard coded in self.models
    """

    # we'll also expose a session as GargTestRunner.testdb_session
    testdb_session = None

    def __init__(self, *args, **kwargs):
        # our custom tables to be created (in correct order)
        self.models = ['ngrams', 'nodes', 'contacts', 'nodes_nodes',  'nodes_ngrams', 'nodes_nodes_ngrams',  'nodes_ngrams_ngrams',  'nodes_hyperdata']
        self.testdb_engine = None

        # and execute default django init
        old_config = super(GargTestRunner, self).__init__(*args, **kwargs)


    def setup_databases(self, *args, **kwargs):
        """
        Complement the database creation
        by our own "models to tables" migration
        """

        # default django setup performs base creation + auto migrations
        old_config = super(GargTestRunner, self).setup_databases(*args, **kwargs)

        # retrieve the testdb_name set by DiscoverRunner
        testdb_names = []
        for db_infos in get_unique_databases_and_mirrors():
            # a key has the form: (IP, port, backend, dbname)
            for key in db_infos:
                # db_infos[key] has the form (dbname, {'default'})
                testdb_names.append(db_infos[key][0])

        # /!\ hypothèse d'une database unique /!\
        testdb_name = testdb_names[0]

        # now we use a copy of our normal db config...
        db_params = DATABASES['default']

        # ...just changing the name
        db_params['NAME'] = testdb_name

        # connect to this test db
        testdb_url = 'postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{NAME}'.format_map(db_params)
        self.testdb_engine = create_engine( testdb_url )
        print("TESTDB INIT: opened connection to database **%s**" % db_params['NAME'])

        # we retrieve real tables declarations from our loaded Base
        sqla_models = (Base.metadata.tables[model_name] for model_name in self.models)

        # example: Base.metadata.tables['ngrams']
        # ---------------------------------------
        # Table('ngrams', Column('id', Integer(), table=<ngrams>, primary_key=True),
        #                 Column('terms', String(length=255), table=<ngrams>),
        #                 Column('n', Integer(), table=<ngrams>),
        #                 schema=None)

        # and now creation of each table in our test db (like dbmigrate)
        for model in sqla_models:
            try:
                model.create(self.testdb_engine)
                print('TESTDB INIT: created model: `%s`' % model)
            except Exception as e:
                print('TESTDB INIT ERROR: could not create model: `%s`, %s' % (model, e))


        # we also create a session to provide it the way we usually do in garg
        # (it's a class based static var to be able to share it with our tests)
        GargTestRunner.testdb_session = scoped_session(sessionmaker(bind=self.testdb_engine))

        # and let's create a user too otherwise we'll never be able to login
        user = User.objects.create_user(username='pcorser', password='peter')

        # old_config will be used by DiscoverRunner
        # (to remove everything at the end)
        return old_config


    def teardown_databases(self, old_config, *args, **kwargs):
        """
        After all tests
        """
        # close the session
        GargTestRunner.testdb_session.close()

        # free the connection
        self.testdb_engine.dispose()

        # default django teardown performs destruction of the test base
        super(GargTestRunner, self).teardown_databases(old_config, *args, **kwargs)
