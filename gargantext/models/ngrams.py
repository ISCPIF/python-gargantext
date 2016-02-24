from gargantext.util.db import *
from gargantext.util.files import upload
from gargantext.constants import *

from .nodes import Node

__all__ = ['Ngram', 'NodeNgram']


class Ngram(Base):
    __tablename__ = 'ngrams'
    id = Column(Integer, primary_key=True)
    terms = Column(String(255), unique=True)
    n = Column(Integer)


class NodeNgram(Base):
    __tablename__ = 'nodes_ngrams'
    node_id = Column(Integer, ForeignKey(Node.id, ondelete='CASCADE'), primary_key=True)
    ngram_id = Column(Integer, ForeignKey(Ngram.id, ondelete='CASCADE'), primary_key=True)
    weight = Column(Float)
