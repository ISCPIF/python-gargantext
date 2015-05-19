from gargantext_web import settings
from node import models


__all__ = ['literalquery', 'session', 'cache', 'Session', 'bulk_insert', 'engine', 'get_cursor']


# initialize sqlalchemy

from sqlalchemy.orm import Session, mapper
from sqlalchemy.ext.automap import automap_base

from sqlalchemy import create_engine, MetaData, Table, Column, ForeignKey
from sqlalchemy.types import Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSON

engine = create_engine('postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}/{NAME}'.format(
    **settings.DATABASES['default']
))
Base = automap_base()

Base.prepare(engine, reflect=True)

# model representation

def model_repr(modelname):
    def _repr(obj):
        result = '<' + modelname
        isfirst = True
        for key, value in obj.__dict__.items():
            if key[0] != '_':
                value = repr(value)
                if len(value) > 64:
                    value = value[:30] + '....' + value[-30:]
                if isfirst:
                    isfirst = False
                else:
                    result += ','
                result += ' ' + key + '=' + value
        result += '>'
        return result
    return _repr

# map the Django models found in node.models to SQLAlchemy models

for model_name, model in models.__dict__.items():
    if hasattr(model, '_meta'):
        table_name = model._meta.db_table
        if hasattr(Base.classes, table_name):
            sqla_model = getattr(Base.classes, table_name)
            setattr(sqla_model, '__repr__', model_repr(model_name))
            globals()[model_name] = sqla_model
            __all__.append(model_name)


NodeNgram = Node_Ngram
NodeResource = Node_Resource

# manually declare the Node table...
from datetime import datetime
from sqlalchemy.types import *
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, aliased

#class Node(Base):
#     __tablename__ = 'node_node'
#     __table_args__ = {'auto_load':True, 'extend_existing':True}
#     id = Column(Integer, primary_key=True)
#     user_id = Column(Integer, ForeignKey('auth_user.id', ondelete='CASCADE'), index=True, nullable=False)
#     type_id = Column(Integer, ForeignKey('node_nodetype.id', ondelete='CASCADE'), index=True, nullable=False)
#     name = Column(String(255))
#     language_id = Column(Integer, ForeignKey('node_language.id', ondelete='CASCADE'), index=True, nullable=False)
#     date = Column(DateTime(), default=datetime.utcnow, nullable=True)
#     hyperdata = Column(JSONB, default={}, nullable=False)
#
#     def __repr__(self):
#        return '<Id %r>' % self.id


# debugging tool, to translate SQLAlchemy queries to string

def literalquery(statement, dialect=None):
    """Generate an SQL expression string with bound parameters rendered inline
    for the given SQLAlchemy statement.

    WARNING: This method of escaping is insecure, incomplete, and for debugging
    purposes only. Executing SQL statements with inline-rendered user values is
    extremely insecure.
    """
    import sqlalchemy.orm
    if isinstance(statement, sqlalchemy.orm.Query):
        if dialect is None:
            dialect = statement.session.get_bind(
                statement._mapper_zero_or_none()
            ).dialect
        statement = statement.statement
    if dialect is None:
        dialect = getattr(statement.bind, 'dialect', None)
    if dialect is None:
        from sqlalchemy.dialects import mysql
        dialect = mysql.dialect()

    Compiler = type(statement._compiler(dialect))

    class LiteralCompiler(Compiler):
        visit_bindparam = Compiler.render_literal_bindparam

        def render_literal_value(self, value, type_):
            return "'" + str(value) + "'"
            if isinstance(value, (float, int)):
                return str(value)
            elif isinstance(value, datetime):
                return repr(str(value))
            else: 
                if isinstance(value, str):
                    return value.encode('UTF-8')
                else:
                    return value

    return LiteralCompiler(dialect, statement)


# SQLAlchemy session management

def get_engine():
    from sqlalchemy import create_engine
    url = 'postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}/{NAME}'.format(
        **settings.DATABASES['default']
    )
    return create_engine(url, use_native_hstore=True)

engine = get_engine()

def get_sessionmaker():
    from sqlalchemy.orm import sessionmaker
    return sessionmaker(bind=engine)

Session = get_sessionmaker()
session = Session()


# SQLAlchemy model objects caching

from sqlalchemy import or_

class ModelCache(dict):

    def __init__(self, model, preload=False):
        self._model = globals()[model.__name__]
        self._columns_names = [column.name for column in model._meta.fields if column.unique]
        self._columns = [getattr(self._model, column_name) for column_name in self._columns_names]
        self._columns_validators = []
        if preload:
            self.preload()

    def __missing__(self, key):
        #print(key)
        conditions = [
            (column == str(key))
            for column in self._columns
            if column.type.python_type == str or key.__class__ == column.type.python_type
        ]
        element = session.query(self._model).filter(or_(*conditions)).first()
        if element is None:
            raise KeyError
        self[key] = element
        return element

    def preload(self):
        self.clear()
        for element in session.query(self._model).all():
            for column_name in self._columns_names:
                key = getattr(element, column_name)
                self[key] = element

class Cache():

    def __getattr__(self, key):
        try:
            model = getattr(models, key)
        except AttributeError:
            raise AttributeError('No such model: `%s`' % key)
        modelcache = ModelCache(model)
        setattr(self, key, modelcache)
        return modelcache

cache = Cache()


# Insert many elements at once

import psycopg2

def get_cursor():
    db_settings = settings.DATABASES['default']
    db = psycopg2.connect(**{
        'database': db_settings['NAME'],
        'user':     db_settings['USER'],
        'password': db_settings['PASSWORD'],
        'host':     db_settings['HOST'],
    })
    return db, db.cursor()

class bulk_insert:

    def __init__(self, table, keys, data, cursor=None):
        # prepare the iterator
        self.iter = iter(data)
        # template
        self.template = '%s' + (len(keys) - 1) * '\t%s' + '\n'
        # prepare the cursor
        if cursor is None:
            db, cursor = get_cursor()
            mustcommit = True
        else:
            mustcommit = False
        # insert data
        if not isinstance(table, str):
            table = table.__table__.name
        cursor.copy_from(self, table, columns=keys)
        # commit if necessary
        if mustcommit:
            db.commit()

    def read(self, size=None):
        try:
            return self.template % tuple(
                str(x).replace('\r', ' ').replace('\n', ' ').replace('\t', ' ').replace("\\","") for x in next(self.iter)
            )
        except StopIteration:
            return ''

    readline = read

