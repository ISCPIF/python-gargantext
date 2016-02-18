from gargantext import settings


# get engine, session, etc.

from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

def get_engine():
    from sqlalchemy import create_engine
    url = 'postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{NAME}'.format(
        **settings.DATABASES['default']
    )
    return create_engine(url, use_native_hstore=True)

engine = get_engine()

Base = declarative_base()

session = scoped_session(sessionmaker(bind=engine))


# tools to build models

from sqlalchemy.types import *
from sqlalchemy.schema import Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict, MutableList


# useful for queries

from sqlalchemy.orm import aliased
from sqlalchemy import func


# bulk insertions

import psycopg2

def get_cursor():
    db_settings = settings.DATABASES['default']
    db = psycopg2.connect(**{
        'database': db_settings['NAME'],
        'user':     db_settings['USER'],
        'password': db_settings['PASSWORD'],
        'host':     db_settings['HOST'],
        'port':     db_settings['PORT']
    })
    return db, db.cursor()

class bulk_insert:

    def __init__(self, table, fields, data, cursor=None):
        # prepare the iterator
        self.iter = iter(data)
        # template
        self.template = '%s' + (len(fields) - 1) * '\t%s' + '\n'
        # prepare the cursor
        if cursor is None:
            db, cursor = get_cursor()
            mustcommit = True
        else:
            mustcommit = False
        # insert data
        if not isinstance(table, str):
            table = table.__tablename__
        cursor.copy_from(self, table, columns=fields)
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


def bulk_insert_ifnotexists(model, uniquekey, fields, data, cursor=None):
    if cursor is None:
        db, cursor = get_cursor()
        mustcommit = True
    else:
        mustcommit = False
    # create temporary table with given data
    sql_columns = 'id INTEGER'
    for field in fields:
        column = getattr(model, field)
        sql_columns += ', %s %s' % (field, column.type, )
    cursor.execute('CREATE TEMPORARY TABLE __tmp__ (%s)' % (sql_columns, ))
    bulk_insert('__tmp__', fields, data, cursor=cursor)
    # update ids of the temporary table
    cursor.execute('''
        UPDATE __tmp__
        SET id = source.id
        FROM {sourcetable} AS source
        WHERE __tmp__.{uniquecolumn} = source.{uniquecolumn}
    '''.format(
        sourcetable = model.__tablename__,
        uniquecolumn = uniquekey,
    ))
    # insert what has not been found to the real table
    cursor.execute('''
        INSERT INTO {sourcetable} ({columns})
        SELECT {columns}
        FROM __tmp__
        WHERE id IS NULL
    '''.format(
        sourcetable = model.__tablename__,
        columns = ', '.join(fields),
    ))
    # retrieve dict associating unique key to id
    cursor.execute('''
        SELECT source.id, source.{uniquecolumn}
        FROM {sourcetable} AS source
        INNER JOIN __tmp__ ON __tmp__.{uniquecolumn} = source.{uniquecolumn}
    '''.format(
        sourcetable = model.__tablename__,
        uniquecolumn = uniquekey,
        columns = ', '.join(fields),
    ))
    result = {
        row[1]: row[0] for row in cursor.fetchall()
    }
    # this is the end!
    if mustcommit:
        db.commit()
    return result
