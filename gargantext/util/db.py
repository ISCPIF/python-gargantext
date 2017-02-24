from gargantext           import settings
from gargantext.util.json import json_dumps


########################################################################
# get engine, session, etc.
########################################################################
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import delete

def get_engine():
    from sqlalchemy import create_engine
    url = 'postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{NAME}'.format(
        **settings.DATABASES['default']
    )
    return create_engine( url
                        , use_native_hstore = True
                        , json_serializer = json_dumps
                        , pool_size=20, max_overflow=0
    )

engine = get_engine()

Base = declarative_base()

session = scoped_session(sessionmaker(bind=engine))


########################################################################
# tools to build models
########################################################################
from sqlalchemy.types import *
from sqlalchemy.schema import Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, DOUBLE_PRECISION
from sqlalchemy.ext.mutable import MutableDict, MutableList
Double = DOUBLE_PRECISION

########################################################################
# useful for queries
########################################################################
from sqlalchemy.orm import aliased
from sqlalchemy import func, desc

########################################################################
# bulk insertions
########################################################################
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
        # see http://www.postgresql.org/docs/9.4/static/sql-copy.html#AEN72054
        try:
            return '\t'.join(
                value.replace('\\', '\\\\').replace('\n', '\\\n').replace('\r', '\\\r').replace('\t', '\\\t')
                if isinstance(value, str) else str(value) if value is not None else '\\N'
                for value in next(self.iter)
            ) + '\n'
        except StopIteration:
            return ''

    readline = read

def bulk_insert_ifnotexists(model, uniquekey, fields, data, cursor=None, do_stats=False):
    """
    Inserts bulk data with an intermediate check on a uniquekey
    (ex: Ngram.terms) to see if the row existed before.

    If the row already existed we just retrieve its id.
    If it didn't exist we create it and retrieve the id.

    Returns a dict {uniquekey => id}

    Option:
        do stats: also returns the number of those that had no previous id
    """
    if cursor is None:
        db, cursor = get_cursor()
        mustcommit = True
    else:
        mustcommit = False
    # create temporary table with given data
    sql_columns = 'id INTEGER'

    cursor.execute('BEGIN WORK;')
    cursor.execute('LOCK TABLE %s IN SHARE ROW EXCLUSIVE MODE;' % model.__tablename__)


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

    if do_stats:
        # remember how many rows we inserted just now
        n_new = cursor.rowcount

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
        # term : new_id
        row[1]: row[0] for row in cursor.fetchall()
    }
    # this is the end!
    cursor.execute('DROP TABLE __tmp__')
    if mustcommit:
        db.commit()

    if do_stats:
        return result, n_new
    else:
        return result

    cursor.execute('COMMIT WORK;')

    cursor.close()

