#from admin.env import *
from admin.utils import PrintException,DebugTime
from django.db import connection, transaction

from sqlalchemy import desc, asc, or_, and_, Date, cast, select
from sqlalchemy import literal_column
from sqlalchemy.orm import aliased
from sqlalchemy.sql import func

from gargantext_web.db import Node, NodeNgram, NodeNgramNgram
from gargantext_web.db import session, cache, get_or_create_node

from collections import defaultdict

import numpy as np
import pandas as pd

from analysis.lists import WeightedMatrix, UnweightedList


def cooc(corpus=None, list_id=None, limit=1000):

    node_cooc = get_or_create_node(nodetype='Cooccurrence', corpus=corpus
                       , name_str="Cooccurrences corpus " + str(corpus.id) + "for list Cvalue" + str(list_id))

    session.query(NodeNgramNgram).filter(NodeNgramNgram.node_id==node_cooc.id).delete()
    session.commit()

    NodeNgramX = aliased(NodeNgram)
    NodeNgramY = aliased(NodeNgram)


    doc_id = cache.NodeType['Document'].id

    #literal_column(str(miam_id)).label("node_id"),
    query = (session.query(NodeNgramX.ngram_id, NodeNgramY.ngram_id, func.count())
             .join(Node, Node.id == NodeNgramX.node_id)
             .join(NodeNgramY, NodeNgramY.node_id == Node.id)

             .filter(Node.parent_id == corpus.id, Node.type_id == doc_id)
             .filter(NodeNgramX.ngram_id < NodeNgramY.ngram_id)

             .group_by(NodeNgramX.ngram_id, NodeNgramY.ngram_id)
             .order_by(func.count())

             .limit(limit)
             )

    cvalue_id = get_or_create_node(nodetype='Cvalue', corpus=corpus).id
    stop_id = get_or_create_node(nodetype='StopList', corpus=corpus).id

    cvalue_list = UnweightedList(session.query(NodeNodeNgram.ngram_id).filter(NodeNodeNgram.nodex_id==cvalue_id).all())
    stop_list = UnweightedList(session.query(NodeNgram.ngram_id).filter(NodeNgram.node_id==stop_id).all())
    matrix = WeightedMatrix(query)

    cooc = matrix & cvalue_list - stop_list
    cooc.save(node_cooc.id)
    return(node_cooc.id)

def coocOld(corpus=None, list_id=None, limit=100):
    '''
    cooc :: Corpus -> Int -> NodeNgramNgram
    '''
    cursor = connection.cursor()

    node_cooc = get_or_create_node(nodetype='Cooccurrence', corpus=corpus
                       , name_str="Cooccurrences corpus " + str(corpus.id) + "for list Cvalue" + str(list_id))

    session.query(NodeNgramNgram).filter(NodeNgramNgram.node_id==node_cooc.id).delete()
    session.commit()

    query_cooc = """
    INSERT INTO node_nodengramngram (node_id, "ngramx_id", "ngramy_id", score)
        SELECT
        %d as node_id,
        ngX.id,
        ngY.id,
        COUNT(*) AS score
    FROM
        node_node AS n  -- the nodes who are direct children of the corpus

    INNER JOIN
        node_node_ngram AS nngX ON nngX.node_id = n.id  --  list of ngrams contained in the node
    INNER JOIN
        node_nodenodengram AS whitelistX ON whitelistX.ngram_id = nngX.ngram_id -- list of ngrams contained in the whitelist and in the node
    INNER JOIN
        node_ngram AS ngX ON ngX.id = whitelistX.ngram_id -- ngrams which are in both

    INNER JOIN
        node_node_ngram AS nngY ON nngY.node_id = n.id
    INNER JOIN
        node_nodenodengram AS whitelistY ON whitelistY.ngram_id = nngY.ngram_id
    INNER JOIN
        node_ngram AS ngY ON ngY.id = whitelistY.ngram_id

    WHERE
        n.parent_id = %s
    AND
        whitelistX.nodex_id = %s
    AND
        whitelistY.nodex_id = %s
    AND
        nngX.ngram_id < nngY.ngram_id   --  so we only get distinct pairs of ngrams

    GROUP BY
        ngX.id,
        ngX.terms,
        ngY.id,
        ngY.terms

    ORDER BY
        score DESC
    LIMIT
        %d
    """ % (node_cooc.id, corpus.id, list_id, list_id, limit)

    # print(query_cooc)
    cursor.execute(query_cooc)
    return(node_cooc.id)

def specificity(cooc_id=None, corpus=None):

    cooccurrences = session.query(NodeNgramNgram).filter(NodeNgramNgram.node_id==cooc_id).all()

    matrix = defaultdict(lambda : defaultdict(float))

    for cooccurrence in cooccurrences:
        matrix[cooccurrence.ngramx_id][cooccurrence.ngramy_id] = cooccurrence.score
        matrix[cooccurrence.ngramy_id][cooccurrence.ngramx_id] = cooccurrence.score

    x = pd.DataFrame(matrix).fillna(0)
    x = x / x.sum(axis=1)

    xs = x.sum(axis=1)
    ys = x.sum(axis=0)

    m = ( xs - ys) / (2 * (x.shape[0] - 1))
    m = m.sort(inplace=False)

    node = get_or_create_node(nodetype='Specificites',corpus=corpus)

    data = zip(  [node.id for i in range(1,m.shape[0])]
               , [corpus.id for i in range(1,m.shape[0])]
               , m.index.tolist()
               , m.values.tolist()
               )
    session.query(NodeNodeNgram).filter(NodeNodeNgram.nodex_id==node.id).delete()
    session.commit()

    bulk_insert(NodeNodeNgram, ['nodex_id', 'nodey_id', 'ngram_id', 'score'], [d for d in data])

def compute_specificity(corpus,limit=100):
    '''
    Computing specificities
    '''
    dbg = DebugTime('Corpus #%d - specificity' % corpus.id)

    list_cvalue = get_or_create_node(nodetype='Cvalue', corpus=corpus)
    cooc_id = cooc(corpus=corpus, list_id=list_cvalue.id,limit=limit)

    specificity(cooc_id=cooc_id,corpus=corpus)
    dbg.show('specificity')


#corpus=session.query(Node).filter(Node.id==244250).first()
#cooc2(corpus)
#compute_specificity(corpus)

