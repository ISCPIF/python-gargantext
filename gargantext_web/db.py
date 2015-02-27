from node import models
from gargantext_web import settings


__all__ = ['literalquery', 'session', 'cache', 'Session']


# map the Django models found in node.models to SQLAlchemy models

for model_name, model in models.__dict__.items():
    if hasattr(model, 'sa'):
        globals()[model_name] = model.sa
        __all__.append(model_name)

NodeNgram = Node_Ngram


# debugging tool, to translate SQLAlchemy queries to string

def literalquery(statement, dialect=None):
    """Generate an SQL expression string with bound parameters rendered inline
    for the given SQLAlchemy statement.

    WARNING: This method of escaping is insecure, incomplete, and for debugging
    purposes only. Executing SQL statements with inline-rendered user values is
    extremely insecure.
    """
    from datetime import datetime
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

def get_sessionmaker():
    from django.db import connections
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    alias = 'default'
    connection = connections[alias]
    url = 'postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}/{NAME}'.format(
        **settings.DATABASES['default']
    )
    engine = create_engine(url, use_native_hstore=True)
    return sessionmaker(bind=engine)

Session = get_sessionmaker()
session = Session()


# SQLAlchemy model objects caching

from sqlalchemy import or_

class ModelCache(dict):

    def __init__(self, model, preload=False):
        self._model = model.sa
        self._columns_names = [column.name for column in model._meta.fields if column.unique]
        self._columns = [getattr(self._model, column_name) for column_name in self._columns_names]
        self._columns_validators = []
        if preload:
            self.preload()

    def __missing__(self, key):
        conditions = [
            (column == key)
            for column in self._columns
            if key.__class__ == column.type.python_type
        ]
        if len(conditions) == 0:
            raise KeyError
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

class Cache:

    def __getattr__(self, key):
        try:
            model = getattr(models, key)
        except AttributeError:
            raise AttributeError('No such model: `%s`' % key)
        modelcache = ModelCache(model)
        setattr(self, key, modelcache)
        return modelcache

cache = Cache()
