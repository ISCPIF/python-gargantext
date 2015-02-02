from node import models
from gargantext_web import settings


Language = models.Language.sa
Metadata = models.Metadata.sa
Ngram = models.Ngram.sa
Node = models.Node.sa
Node_Metadata = models.Node_Metadata.sa
NodeNgram = Node_Ngram = models.Node_Ngram.sa
NodeNodeNgram = models.NodeNgramNgram.sa
NodeType = models.NodeType.sa
Resource = models.Resource.sa
ResourceType = models.ResourceType.sa


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
