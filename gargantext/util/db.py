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

from sqlalchemy.orm import aliased, synonym
from sqlalchemy.types import *
from sqlalchemy.schema import Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
