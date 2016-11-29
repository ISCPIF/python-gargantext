from gargantext.util.db import *
from gargantext.util.files import upload
from gargantext.constants import *

from datetime import datetime

from .users import User

__all__ = ['Node', 'NodeNode']

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

class Node(Base):
    """This model can fit many purposes.
    It intends to provide a generic model, allowing hierarchical structure
    and NoSQL-like data structuring.
    The possible types are defined in `gargantext.constants.NODETYPES`.
    """
    __tablename__ = 'nodes'
    id = Column(Integer, primary_key=True)
    typename = Column(NodeType, index=True)
    # foreign keys
    user_id = Column(Integer, ForeignKey(User.id, ondelete='CASCADE'))
    parent_id = Column(Integer, ForeignKey('nodes.id', ondelete='CASCADE'))
    # main data
    name = Column(String(255))
    date  = Column(DateTime(), default=datetime.now)
    # metadata (see https://bashelton.com/2014/03/updating-postgresql-json-fields-via-sqlalchemy/)
    hyperdata = Column(JSONB, default=dict)

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

    def resources(self):
        """Return all the resources attached to a given node.
        Mainly used for corpora.

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
        Mainly used for corpora.

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

class NodeNode(Base):
    __tablename__ = 'nodes_nodes'
    node1_id = Column(Integer, ForeignKey(Node.id, ondelete='CASCADE'), primary_key=True)
    node2_id = Column(Integer, ForeignKey(Node.id, ondelete='CASCADE'), primary_key=True)
    score    = Column(Float(precision=24))
