from gargantext.util.db import *

from .nodes import Node

__all__ = ['Ngram', 'NodeNgram', 'NodeNodeNgram', 'NodeNgramNgram']


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

class NodeNodeNgram(Base):
    """ for instance for TFIDF
    (
        doc                              ::Node ,
        corpus                           ::Node ,
        word                             ::Ngram ,
        tfidf of ngram in doc in corpus  ::Float (real)
    )
    """
    __tablename__ = 'nodes_nodes_ngrams'
    node1_id = Column(Integer, ForeignKey(Node.id, ondelete='CASCADE'), primary_key=True)
    node2_id = Column(Integer, ForeignKey(Node.id, ondelete='CASCADE'), primary_key=True)
    ngram_id = Column(Integer, ForeignKey(Ngram.id, ondelete='CASCADE'), primary_key=True)
    score = Column(Float(precision=24))
    # précision max 24 bit pour un type sql "real" (soit 7 chiffres après virgule)
    # sinon par défaut on aurait un type sql "double_precision" (soit 15 chiffres)
    # (cf. www.postgresql.org/docs/9.4/static/datatype-numeric.html#DATATYPE-FLOAT)

class NodeNgramNgram(Base):
    """ for instance for COOCCURRENCES and GROUPLIST
    (
        cooc_node/group_node  ::Node ,
        term_A                ::Ngram ,
        term_B                ::Ngram ,
        weight                ::Float (real)
    )
    """
    __tablename__ = 'nodes_ngrams_ngrams'
    node_id = Column(Integer, ForeignKey(Node.id, ondelete='CASCADE'), primary_key=True)
    ngram1_id = Column(Integer, ForeignKey(Ngram.id, ondelete='CASCADE'), primary_key=True)
    ngram2_id = Column(Integer, ForeignKey(Ngram.id, ondelete='CASCADE'), primary_key=True)
    weight = Column(Float(precision=24))  # see comment for NodeNodeNgram.score
