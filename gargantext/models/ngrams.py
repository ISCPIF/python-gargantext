from .base import Base, Column, ForeignKey, relationship, Index, \
                  Integer, Float, String
from .nodes import Node

__all__ = ['Ngram', 'NodeNgram', 'NodeNodeNgram', 'NodeNgramNgram']


class Ngram(Base):
    __tablename__ = 'ngrams'
    __table_args__ = (
            Index('ngrams_id_n_idx', 'id', 'n'),
            Index('ngrams_n_idx', 'n'))

    id = Column(Integer, primary_key=True)
    terms = Column(String(255), unique=True)
    n = Column(Integer)

    def __str__(self):
        return '<{0.terms}>#{0.n}'.format(self)

    def __repr__(self):
        return '<Ngram(id={0.id}, terms={0.terms!r}, n={0.n})>'.format(self)


class NodeNgram(Base):
    __tablename__ = 'nodes_ngrams'
    __table_args__ = (
            Index('nodes_ngrams_node_id_ngram_id_idx', 'node_id', 'ngram_id'),
            Index('nodes_ngrams_node_id_idx', 'node_id'),
            Index('nodes_ngrams_ngram_id_idx', 'ngram_id'))

    node_id = Column(Integer, ForeignKey(Node.id, ondelete='CASCADE'), primary_key=True)
    ngram_id = Column(Integer, ForeignKey(Ngram.id, ondelete='CASCADE'), primary_key=True)
    weight = Column(Float)

    node = relationship(Node)
    ngram = relationship(Ngram)

    def __repr__(self):
        return '<NodeNgram(node_id={0.node_id}, ngram={0.ngram}, weight={0.weight})>'.format(self)


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
    __table_args__ = (
            Index('nodes_nodes_ngrams_node2_id_idx', 'node2_id'),
            Index('nodes_nodes_ngrams_node1_id_idx', 'node1_id'))

    node1_id = Column(Integer, ForeignKey(Node.id, ondelete='CASCADE'), primary_key=True)
    node2_id = Column(Integer, ForeignKey(Node.id, ondelete='CASCADE'), primary_key=True)
    ngram_id = Column(Integer, ForeignKey(Ngram.id, ondelete='CASCADE'), primary_key=True)
    score = Column(Float(precision=24))
    # précision max 24 bit pour un type sql "real" (soit 7 chiffres après virgule)
    # sinon par défaut on aurait un type sql "double_precision" (soit 15 chiffres)
    # (cf. www.postgresql.org/docs/9.4/static/datatype-numeric.html#DATATYPE-FLOAT)

    node1 = relationship(Node, foreign_keys=[node1_id])
    node2 = relationship(Node, foreign_keys=[node2_id])
    ngram = relationship(Ngram)

    def __repr__(self):
        return '<NodeNodeNgram(node1_id={0.node1_id}, node2_id={0.node2_id}, ngram={0.ngram}, score={0.score})>'.format(self)


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
    __table_args__ = (
            Index('nodes_ngrams_ngrams_node_id_ngram1_id_ngram2_id_idx', 'node_id', 'ngram1_id', 'ngram2_id'),
            Index('nodes_ngrams_ngrams_node_id_idx', 'node_id'),
            Index('nodes_ngrams_ngrams_ngram1_id_idx', 'ngram1_id'),
            Index('nodes_ngrams_ngrams_ngram2_id_idx', 'ngram2_id'))

    node_id = Column(Integer, ForeignKey(Node.id, ondelete='CASCADE'), primary_key=True)
    ngram1_id = Column(Integer, ForeignKey(Ngram.id, ondelete='CASCADE'), primary_key=True)
    ngram2_id = Column(Integer, ForeignKey(Ngram.id, ondelete='CASCADE'), primary_key=True)
    weight = Column(Float(precision=24))  # see comment for NodeNodeNgram.score

    node = relationship(Node)
    ngram1 = relationship(Ngram, foreign_keys=[ngram1_id])
    ngram2 = relationship(Ngram, foreign_keys=[ngram2_id])

    def __repr__(self):
        return '<NodeNgramNgram(node_id={0.node_id}, ngram1={0.ngram1}, ngram2={0.ngram2}, weight={0.weight})>'.format(self)
