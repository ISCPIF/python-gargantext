from gargantext.util.db import session
from gargantext.util.files import upload
from gargantext.constants import *

from datetime import datetime

from .base import Base, Column, ForeignKey, relationship, TypeDecorator, Index, \
                  Integer, Float, String, DateTime, JSONB, TSVectorType, \
                  MutableList, MutableDict, validates, ValidatorMixin, text
from .users import User

__all__ = ['Node', 'NodeNode', 'CorpusNode']

class NodeType(TypeDecorator):
    """Define a new type of column to describe a Node's type.
    Internally, this column type is implemented as an SQL integer.
    Values are detailed in `gargantext.constants.NODETYPES`.
    """
    impl = Integer
    def process_bind_param(self, typename, dialect):
        return NODETYPES.index(typename)
    def process_result_value(self, typeindex, dialect):
        return NODETYPES[typeindex]


class Node(ValidatorMixin, Base):
    """This model can fit many purposes:

    myFirstCorpus = session.query(CorpusNode).first()

    It intends to provide a generic model, allowing hierarchical structure
    and NoSQL-like data structuring.
    The possible types are defined in `gargantext.constants.NODETYPES`.

    Thanks to __new__ overriding and SQLAlchemy's polymorphism, every Node
    instance is automagically casted to its sub-class, assuming a typename
    is specified.

    >>> Node(name='without-type')
    <Node(id=None, typename=None, user_id=None, parent_id=None, name='without-type', date=None)>
    >>> Node(typename='CORPUS')
    <CorpusNode(id=None, typename='CORPUS', user_id=None, parent_id=None, name=None, date=None)>
    >>> from gargantext.util.db import session
    >>> session.query(Node).filter_by(typename='USER').first() # doctest: +ELLIPSIS
    <UserNode(...)>

    But beware, there are some pitfalls with bulk queries. In this case typename
    MUST be specified manually.

    >>> session.query(UserNode).delete() # doctest: +SKIP
    # Wrong: all nodes are deleted!
    >>> session.query(UserNode).filter_by(typename='USER').delete() # doctest: +SKIP
    # Right: only user nodes are deleted.
    """
    __tablename__ = 'nodes'
    __table_args__ = (
            Index('nodes_user_id_typename_parent_id_idx', 'user_id', 'typename', 'parent_id'),
            Index('nodes_hyperdata_idx', 'hyperdata', postgresql_using='gin'))

    id = Column(Integer, primary_key=True)

    typename = Column(NodeType, index=True, nullable=False)
    __mapper_args__ = { 'polymorphic_on': typename }

    # foreign keys
    user_id       = Column(Integer, ForeignKey(User.id, ondelete='CASCADE'),
                           nullable=False,
                           server_default=text('current_user_id()'))
    user          = relationship(User)

    parent_id     = Column(Integer, ForeignKey('nodes.id', ondelete='CASCADE'))
    parent        = relationship('Node', remote_side=[id])

    name = Column(String(255), nullable=False, server_default='')
    date = Column(DateTime(timezone=True), nullable=False,
                  server_default=text('CURRENT_TIMESTAMP'))

    hyperdata = Column(JSONB, default=dict, nullable=False,
                       server_default=text("'{}'::jsonb"))

    # Create a TSVECTOR column to use fulltext search feature of PostgreSQL.
    # We need to create a trigger to update this column on update and insert,
    # it's created in alembic/version/1fb4405b59e1_add_english_fulltext_index_on_nodes_.py
    #
    # To use this column: session.query(DocumentNode) \
    #                            .filter(Node.title_abstract.match('keyword'))
    title_abstract = Column(TSVectorType(regconfig='english'))

    def __new__(cls, *args, **kwargs):
        if cls is Node and kwargs.get('typename'):
            typename = kwargs.pop('typename')
            return _NODE_MODELS[typename](*args, **kwargs)
        return super(Node, cls).__new__(cls)

    def __init__(self, **kwargs):
        """Node's constructor.
        Initialize the `hyperdata` as a dictionary if no value was given.
        """
        if 'hyperdata' not in kwargs:
            kwargs['hyperdata'] = kwargs.get('hyperdata', MutableDict())
        Base.__init__(self, **kwargs)

    def __getitem__(self, key):
        """Allow direct access to hyperdata via the bracket operator.
        """
        return self.hyperdata[key]

    def __setitem__(self, key, value):
        """Allow direct access to hyperdata via the bracket operator.
        """
        self.hyperdata[key] = value

    def __repr__(self):
        return '<{0.__class__.__name__}(id={0.id}, typename={0.typename!r}, ' \
               'user_id={0.user_id}, parent_id={0.parent_id}, ' \
               'name={0.name!r}, date={0.date})>'.format(self)

    @validates('name')
    def validate_name(self, key, value):
        return self.enforce_length(key, value)

    @property
    def ngrams(self):
        """Pseudo-attribute allowing to retrieve a node's ngrams.
        Returns a query (which can be further filtered), of which returned rows
        are the ngram's weight for this node and the ngram.
        """
        from . import NodeNgram, Ngram
        query = (session
            .query(NodeNgram.weight, Ngram)
            .select_from(NodeNgram)
            .join(Ngram)
            .filter(NodeNgram.node_id == self.id)
        )
        return query

    def as_list(self):
        """Retrieve the current node as a list/matrix of ngrams identifiers.
        See `gargantext.util.lists` and `gargantext.constants.LISTTYPES`
        for more info.
        """
        try:
            return LISTTYPES[self.typename](self.id)
        except KeyError:
            raise ValueError('This node\'s typename is not convertible to a list: %s (accepted values: %s)' % (
                self.typename,
                ', '.join(LISTTYPES.keys())
            ))

    def save_hyperdata(self):
        """This is a necessary, yet ugly trick.
        Indeed, PostgreSQL does not yet manage incremental updates (see
        https://bashelton.com/2014/03/updating-postgresql-json-fields-via-sqlalchemy/)
        """
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(self, 'hyperdata')
        # # previous trick (even super-uglier)
        # hyperdata = self.hyperdata
        # self.hyperdata = None
        # session.add(self)
        # session.commit()
        # self.hyperdata = hyperdata
        # session.add(self)
        # session.commit()

    def children(self, typename=None, order=None):
        """Return a query to all the direct children of the current node.
        Allows filtering by typename (see `constants.py`)
        """
        query = session.query(Node).filter(Node.parent_id == self.id)
        if typename is not None:
            query = query.filter(Node.typename == typename)

        if order is not None:
            query = query.order_by(Node.name)
        return query

    def add_child(self, **kwargs):
        """Create and return a new direct child of the current node.
        """
        return Node(
            user_id = self.user_id,
            parent_id = self.id,
            **kwargs
        )

    def status(self, action=None, progress=0, complete=False, error=None):
        """Get or update the status of the given action.
        If no action is given, the status of the first uncomplete or last item
        is returned.
        The `complete` parameter should be a boolean.
        The `error` parameter should be an exception.
        """
        date = datetime.now()
        # if the hyperdata do not have data about status
        if 'statuses' not in self.hyperdata:
            self['statuses'] = MutableList()
        # if no action name is given, return the last appended status
        if action is None:
            for status in self['statuses']:
                if not status['complete']:
                    return status
            if len(self['statuses']):
                return self['statuses'][-1]
            return None
        # retrieve the status concerning by the given action name
        for status in self['statuses']:
            if status['action'] == action:
                if error:
                    status['error'] = error
                if progress:
                    status['progress'] = progress
                if complete:
                    status['complete'] = complete
                if error or progress or complete:
                    status['date'] = date
                return status
        # if no status has been found for the action, append a new one
        self['statuses'].append(MutableDict(
            {'action':action, 'progress':progress, 'complete':complete, 'error':error, 'date':date}
        ))
        return self['statuses'][-1]


class CorpusNode(Node):
    __mapper_args__ = {
        'polymorphic_identity': 'CORPUS'
    }

    def resources(self):
        """Return all the resources attached to a given node.

        example:
        [{'extracted': True,
          'path': '/home/me/gargantext/uploads/corpora/0c/0c5b/0c5b50/0c5b50ad8ebdeb2ae33d8e54141a52ee_Corpus_Europresse-Français-2015-12-11.zip',
          'type': 1,
          'url': None}]
        """
        if 'resources' not in self.hyperdata:
            self['resources'] = MutableList()
        return self['resources']

    def add_resource(self, type, path=None, url=None):
        """Attach a resource to a given node.

        this just adds metadata to the CORPUS node (NOT for adding documents)

        example:
        {'extracted': True,
          'path': '/home/me/gargantext/uploads/corpora/0c/0c5b/0c5b50/0c5b50ad8ebdeb2ae33d8e54141a52ee_Corpus_Europresse-Français-2015-12-11.zip',
          'type': 1,
          'url': None}
        """
        self.resources().append(MutableDict(
            {'type': type, 'path':path, 'url':url, 'extracted': False}
        ))


class NodeNode(Base):
    __tablename__ = 'nodes_nodes'
    __table_args__ = (
            Index('nodes_nodes_node1_id_node2_id_idx', 'node1_id', 'node2_id'),)

    node1_id = Column(Integer, ForeignKey(Node.id, ondelete='CASCADE'), primary_key=True)
    node2_id = Column(Integer, ForeignKey(Node.id, ondelete='CASCADE'), primary_key=True)
    score    = Column(Float(precision=24))

    node1 = relationship(Node, foreign_keys=[node1_id])
    node2 = relationship(Node, foreign_keys=[node2_id])

    def __repr__(self):
        return '<NodeNode(node1_id={0.node1_id}, node2_id={0.node2_id}, score={0.score})>'.format(self)


# --8<-- Begin hack ------

# XXX Hack to automatically defines subclasses of Node for every NODETYPES,
#     in order to avoid SQLAlchemy complaints -- and subsequent exceptions.
#
#     We could manually write a class for every NodeType, or find a way to
#     tell SQLAlchemy that it should stick to instantiate a Node when a
#     class is not defined for the wanted typename.

_ALREADY_IMPLEMENTED_NODE_TYPES = \
    set(cls.__mapper_args__.get('polymorphic_identity') for cls in Node.__subclasses__())

for nodetype in NODETYPES:
    if nodetype and nodetype not in _ALREADY_IMPLEMENTED_NODE_TYPES:
        # Convert nodetype to a CamelCase class name, assuming it's possible...
        class_name = ''.join(nodetype.title().split("-")) + 'Node'
        # Create new class and add it to global scope
        globals()[class_name] = type(class_name, (Node,), {
            "__mapper_args__": {
                "polymorphic_identity": nodetype
            }
        })
        # Add class to exports
        __all__.append(class_name)

# ------ End of hack ------

_NODE_MODELS = {
    mapper.polymorphic_identity: mapper.class_
    for mapper in Node.__mapper__.self_and_descendants
    if mapper.class_ is not Node
}
