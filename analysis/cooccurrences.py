from env import *

from admin.utils import PrintException

from gargantext_web.db import NodeNgram
from gargantext_web.db import *
from parsing.corpustools import *

import sqlalchemy
from sqlalchemy.sql import func
from sqlalchemy import desc, asc, or_, and_, Date, cast, select
from sqlalchemy import literal_column
from sqlalchemy.orm import aliased

# from gargantext_web.db import Node, get_cursor

def cooccurrences(user_id=None, corpus_id=None,
                mainlist_id=None, stoplist_id=None,
                lem=False, stem=True, cvalue=False,
                date_begin=None, date_end=None,
                size=10, n_min=2, n_max=3):
    '''
    Function to create a cooccurrence Node
    ---------------------------------------------------
    cooccurrences :: [Text] -> [Word] -> [[Word]]

    user_id      :: Integer, User.id who creates the cooccurrence matrix
    corpus_id    :: Integer, Node.id with NodeType "Corpus"

    miamlist_id  :: Integer, Node.id with NodeType "MiamList" and with parent_id=corpus_id
    stoplist_id  :: Integer, Node.id with NodeType "StopList" and with parent_id=corpus_id
    mainlist_id  :: Integer, Node.id with NodeType "MainList" and with parent_id=corpus_id

    lem          :: False | True, if lemmatization  should be taken into account
    stem         :: False | True, if stemmatization should be taken into account
    cvalue       :: False | True, if cvalue         should be taken into account
    group        :: False | True, if manual groups  should be taken into account

    date_begin   :: Datetime, format YYYY-MM-DD, begin of corpus splitted by date
    date_end     :: Datetime, format YYYY-MM-DD, end   of corpus splitted by date

    size         :: Integer, size of the cooccurrence list
    n_min        :: Integer, minimal ngram's size of n
    n_max        :: Integer, maximal ngram's size of n
    '''

    # We create a new node of Type cooccurrence
    if corpus_id is not None and user_id is not None:
        node_cooc = session.query(Node).filter(
                                Node.parent_id==corpus.id,
                                Node.type_id == cache.NodeType['Cooccurrence'].id
                                ).first()
        if node_cooc is None:
            node_cooc = Node(user_id = user_id,
                             parent_id=corpus_id,
                             type_id=cache.NodeType['Cooccurrence'].id,
                             name="Cooccurrences corpus " + str(corpus_id))

            session.add(node_cooc)
            session.commit()
    else:
        print("Usage (Warning): Need corpus_id and user_id")

    # Getting the main lists here, by default create or take the first one.

    # Getting nodes for lems, stems and cvalue, if needed.
    if stem is True:
        node_stem = session.query(Node).filter(
            Node.type_id==cache.NodeType['Stem'].id).first()

    miamNgram   = aliased(NodeNgram)
    stopNgram   = aliased(NodeNgram)
    groupNgram   = aliased(NodeNgramNgram)

    stemNgram   = aliased(NodeNgramNgram)
    lemNgram    = aliased(NodeNgramNgram)
    cvalueNgram = aliased(NodeNgramNgram)


    # Literal query here
    query = (session.query(Node.id, Ngram.id.label('x'), Ngram.id.label('y'), func.count().label('score'))
        .join(NodeNgram, NodeNgram.node_id == Node.id)
        #.outerjoin(stopNgram, stopNgram.ngram_id == Ngram.id)
        .filter(Node.parent_id == corpus_id)
        .filter(Node.type_id == cache.NodeType['Document'].id)
        #.filter(Ngram.n > n_max)
        #.group_by(x)
        #.group_by(y)
        #.limit(size)
        .all()
        )

    return(query)

