"""
A test runner derived from default (DiscoverRunner) but adapted to our custom DB

cf. docs.djangoproject.com/en/1.9/topics/testing/advanced/#using-different-testing-frameworks
cf. gargantext/settings.py => TEST_RUNNER
cf. dbmigrate.py
cf ./session_and_db_remarks.md
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

# hack to make our minimal django use the same test DB settings as DiscoverRunner
# (more details: cf ./session_and_db_remarks.md)
DATABASES['default']['NAME'] = DATABASES['default']['TEST']['NAME']

setup()   # models can now be imported
from gargantext import models # Base is now filled
from gargantext.util.db  import Base  # contains metadata.tables
# ------------------------------------------------------------------------------

# thanks to our hack, util.db.engine and util.db.session already use the test DB
from gargantext.util.db import engine, session


class GargTestRunner(DiscoverRunner):
    """
    We use the default test runner but we just add
    our own dbmigrate elements at db creation

    1) we let django.test.runner do the test db creation + auto migrations
    2) we create tables for our models like in dbmigrate with the test engine

    POSSIBLE: definitions of tables to be created should be fully hard coded like the list in self.models
    => then remove django.setup() used to import models and DATABASES renaming to prevent its secondary effects
    """

    def __init__(self, *args, **kwargs):
        # our custom tablenames to be created (in correct order)
        self.models = ['ngrams', 'nodes', 'contacts', 'nodes_nodes',  'nodes_ngrams', 'nodes_nodes_ngrams',  'nodes_ngrams_ngrams',  'nodes_hyperdata']

        # POSSIBLE: hard-code here our custom table declarations
        # self.tables = [Table('ngrams', MetaData(bind=None)....)]

        # and execute default django unittests init
        old_config = super(GargTestRunner, self).__init__(*args, **kwargs)


    def setup_databases(self, *args, **kwargs):
        """
        Complement the database creation
        by our own "models to tables" migration
        """

        # default django setup performs base creation + auto migrations
        old_config = super(GargTestRunner, self).setup_databases(*args, **kwargs)

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
                model.create(engine)
                print('TESTDB INIT: created model: `%s`' % model)
            except Exception as e:
                print('TESTDB INIT ERROR: could not create model: `%s`, %s' % (model, e))

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
        session.close()

        # free the connection
        engine.dispose()

        # default django teardown performs destruction of the test base
        super(GargTestRunner, self).teardown_databases(old_config, *args, **kwargs)




# snippets if we choose direct model building instead of setup() and Base.metadata.tables[model_name]
# from sqlalchemy.types import Integer, String, DateTime, Text, Boolean, Float
# from gargantext.models.nodes import NodeType
# from gargantext.models.hyperdata import HyperdataKey
# from sqlalchemy.schema import Table, Column, ForeignKey, UniqueConstraint, MetaData
# from sqlalchemy.dialects.postgresql import JSONB, DOUBLE_PRECISION
# from sqlalchemy.ext.mutable import MutableDict, MutableList
# Double = DOUBLE_PRECISION

# sqla_models = [i for i in sqla_models]
# print (sqla_models)
# sqla_models = [Table('ngrams', MetaData(bind=None), Column('id', Integer(), primary_key=True, nullable=False), Column('terms', String(length=255)), Column('n', Integer()), schema=None), Table('nodes', MetaData(bind=None), Column('id', Integer(), primary_key=True, nullable=False), Column('typename', NodeType()), Column('user_id', Integer(), ForeignKey('auth_user.id')), Column('parent_id', Integer(), ForeignKey('nodes.id')), Column('name', String(length=255)), Column('date', DateTime()), Column('hyperdata', JSONB(astext_type=Text())), schema=None), Table('contacts', MetaData(bind=None), Column('id', Integer(), primary_key=True, nullable=False), Column('user1_id', Integer(), primary_key=True, nullable=False), Column('user2_id', Integer(), primary_key=True, nullable=False), Column('is_blocked', Boolean()), Column('date_creation', DateTime()), schema=None), Table('nodes_nodes', MetaData(bind=None), Column('node1_id', Integer(), ForeignKey('nodes.id'), primary_key=True, nullable=False), Column('node2_id', Integer(), ForeignKey('nodes.id'), primary_key=True, nullable=False), Column('score', Float(precision=24)), schema=None), Table('nodes_ngrams', MetaData(bind=None), Column('node_id', Integer(), ForeignKey('nodes.id'), primary_key=True, nullable=False), Column('ngram_id', Integer(), ForeignKey('ngrams.id'), primary_key=True, nullable=False), Column('weight', Float()), schema=None), Table('nodes_nodes_ngrams', MetaData(bind=None), Column('node1_id', Integer(), ForeignKey('nodes.id'), primary_key=True, nullable=False), Column('node2_id', Integer(), ForeignKey('nodes.id'), primary_key=True, nullable=False), Column('ngram_id', Integer(), ForeignKey('ngrams.id'), primary_key=True, nullable=False), Column('score', Float(precision=24)), schema=None), Table('nodes_ngrams_ngrams', MetaData(bind=None), Column('node_id', Integer(), ForeignKey('nodes.id'), primary_key=True, nullable=False), Column('ngram1_id', Integer(), ForeignKey('ngrams.id'), primary_key=True, nullable=False), Column('ngram2_id', Integer(), ForeignKey('ngrams.id'), primary_key=True, nullable=False), Column('weight', Float(precision=24)), schema=None), Table('nodes_hyperdata', MetaData(bind=None), Column('id', Integer(), primary_key=True, nullable=False), Column('node_id', Integer(), ForeignKey('nodes.id')), Column('key', HyperdataKey()), Column('value_int', Integer()), Column('value_flt', DOUBLE_PRECISION()), Column('value_utc', DateTime(timezone=True)), Column('value_str', String(length=255)), Column('value_txt', Text()), schema=None)]
