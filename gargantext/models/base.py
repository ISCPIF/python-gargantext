from sqlalchemy.schema import Column, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship, validates
from sqlalchemy.types import TypeDecorator, \
                             Integer, REAL, Boolean, DateTime, String, Text
from sqlalchemy_utils.types import TSVectorType
from sqlalchemy.dialects.postgresql import JSONB, DOUBLE_PRECISION as Double
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import text

__all__ = ["Column", "ForeignKey", "UniqueConstraint", "Index", "relationship",
           "text",
           "validates", "ValidatorMixin",
           "Integer", "Float", "Boolean", "DateTime", "String", "Text",
           "TSVectorType",
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


class Float(REAL):
    """Reflect exact REAL type for PostgreSQL in order to avoid confusion
    within Alembic type comparison"""

    def __init__(self, *args, **kwargs):
        if kwargs.get('precision') == 24:
            kwargs.pop('precision')
        super(Float, self).__init__(*args, **kwargs)


class ValidatorMixin(object):
    def enforce_length(self, key, value):
        """Truncate a string according to its column length

        Usage example:

        .. code-block:: python

            @validates('some_column')
            def validate_some_column(self, key, value):
                self.enforce_length(key, value)
        """
        max_len = getattr(self.__class__, key).prop.columns[0].type.length
        if value and len(value) > max_len:
            return value[:max_len]
        return value
