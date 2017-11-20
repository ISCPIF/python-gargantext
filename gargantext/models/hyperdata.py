from gargantext.constants import INDEXED_HYPERDATA

from .base import Base, Column, ForeignKey, TypeDecorator, Index, \
                  Integer, Double, DateTime, String, Text
from .nodes import Node
import datetime


__all__ = ['NodeHyperdata', 'HyperdataKey']


class classproperty(object):
    """See: http://stackoverflow.com/a/3203659/734335
    """
    def __init__(self, getter):
        self.getter = getter
    def __get__(self, instance, owner):
        return self.getter(owner)


class HyperdataValueComparer(object):
    """This class is there to allow hyperdata comparison.
    Its attribute are overrided at the end of the present module to fit those
    of the `value_flt` and `value_str` attributes of the `NodeHyperdata` class.
    """


class HyperdataKey(TypeDecorator):
    """Define a new type of column to describe a Hyperdata field's type.
    Internally, this column type is implemented as an SQL integer.
    Values are detailed in `gargantext.constants.INDEXED_HYPERDATA`.
    """
    impl = Integer
    def process_bind_param(self, keyname, dialect):
        if keyname in INDEXED_HYPERDATA:
            return INDEXED_HYPERDATA[keyname]['id']
        raise ValueError('Hyperdata key "%s" was not found in `gargantext.constants.INDEXED_HYPERDATA`' % keyname)
    def process_result_value(self, keyindex, dialect):
        for keyname, keysubhash in INDEXED_HYPERDATA.items():
            if keysubhash['id'] == keyindex:
                return keyname
        raise ValueError('Hyperdata key with id=%d was not found in `gargantext.constants.INDEXED_HYPERDATA`' % keyindex)


class NodeHyperdata(Base):
    """This model's primary role is to allow better indexation of hyperdata.
    It stores values contained in the `nodes.hyperdata` column (only those
    listed in `gargantext.constants.INDEXED_HYPERDATA`), associated with the
    corresponding key's index, and hyperdata value.

    Example:
        query = (session
            .query(Node)
            .join(NodeHyperdata)
            .filter(NodeHyperdata.key == 'title')
            .filter(NodeHyperdata.value.startswith('Bees'))
        )

    Example:
        query = (session
            .query(Node)
            .join(NodeHyperdata)
            .filter(NodeHyperdata.key == 'publication_date')
            .filter(NodeHyperdata.value > datetime.datetime.now())
        )
    """
    __tablename__ = 'nodes_hyperdata'
    __table_args__ = (
            Index('nodes_hyperdata_node_id_value_utc_idx', 'node_id', 'value_utc'),
            Index('nodes_hyperdata_node_id_key_value_utc_idx', 'node_id', 'key', 'value_utc'),
            Index('nodes_hyperdata_node_id_key_value_str_idx', 'node_id', 'key', 'value_str'),
            Index('nodes_hyperdata_node_id_key_value_int_idx', 'node_id', 'key', 'value_int'),
            Index('nodes_hyperdata_node_id_key_value_flt_idx', 'node_id', 'key', 'value_flt'),
            Index('nodes_hyperdata_node_id_key_idx', 'node_id', 'key'))

    id        = Column( Integer, primary_key=True )
    node_id   = Column( Integer, ForeignKey(Node.id, ondelete='CASCADE'))
    key       = Column( HyperdataKey )
    value_int = Column( Integer                 , index=True )
    value_flt = Column( Double()                , index=True )
    value_utc = Column( DateTime(timezone=True) , index=True )
    value_str = Column( String(255)             , index=True )
    value_txt = Column( Text                    , index=False )


    def __init__(self, node=None, key=None, value=None):
        """Custom constructor
        """
        # node reference
        if node is not None:
            if hasattr(node, 'id'):
                self.node_id = node.id
            else:
                self.node_id = node
        # key
        if key is not None:
            self.key = key
        # value
        self.value = value

    # FIXME
    @property
    def value(self):
        """Pseudo-attribute used to extract the value in the right format.
        """
        key = INDEXED_HYPERDATA[self.key]
        return key['convert_from_db'](
            self.value_flt if (self.value_str is None) else self.value_str
        )

    @value.setter
    def value(self, value):
        """Pseudo-attribute used to insert the value in the right format.
        """
        key = INDEXED_HYPERDATA[self.key]
        value = key['convert_to_db'](value)
        if isinstance(value, str):
            self.value_str = value
        else:
            self.value_flt = value

    @classproperty  #Pylint don't know @classproperty
    def value(cls): #pylint: disable=method-hidden, no-self-argument
        """Pseudo-attribute used for hyperdata comparison inside a query.
        """
        return HyperdataValueComparer()


def HyperdataValueComparer_overrider(key):
    def comparator(self, *args):
        if len(args) == 0:
            return
        if isinstance(args[0], datetime.datetime):
            args = tuple(map(datetime.datetime.timestamp, args))
        if isinstance(args[0], (int, float)):
            return getattr(NodeHyperdata.value_flt, key)(*args)
        if isinstance(args[0], str):
            return getattr(NodeHyperdata.value_str, key)(*args)
    return comparator
# ??
for key in set(dir(NodeHyperdata.value_flt) + dir(NodeHyperdata.value_str)):
    if key in ( '__dict__'
              , '__weakref__'
              , '__repr__'
              , '__str__')      \
              or 'attr' in key  \
              or 'class' in key \
              or 'init' in key  \
              or 'new' in key :
        continue
    setattr(HyperdataValueComparer, key, HyperdataValueComparer_overrider(key))
