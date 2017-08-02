from sqlalchemy.schema import Column, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, \
                             Integer, Float, Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, DOUBLE_PRECISION as Double
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.ext.declarative import declarative_base

__all__ = ["Column", "ForeignKey", "UniqueConstraint", "relationship",
           "Integer", "Float", "Boolean", "DateTime", "String", "Text",
           "TypeDecorator",
           "JSONB", "Double",
           "MutableDict", "MutableList",
           "Base", "DjangoBase"]


# All the models should derive from this base class, so Base.metadata keeps
# all tables handled by Alembic migration scripts.
Base = declarative_base()

# To be used by tables already handled by Django ORM, such as User model. We
# separate them in order to keep those out of Alembic sight.
DjangoBase = declarative_base()
