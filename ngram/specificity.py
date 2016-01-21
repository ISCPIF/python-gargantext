#from admin.env import *
import inspect

from admin.utils import PrintException,DebugTime
from django.db import connection, transaction

from collections import defaultdict

import numpy as np
import pandas as pd

from analysis.cooccurrences import do_cooc
from gargantext_web.db import get_session, cache, get_or_create_node, bulk_insert
from gargantext_web.db import NodeNgramNgram, NodeNodeNgram

from sqlalchemy import desc, asc, or_, and_, Date, cast, select

def specificity(cooc_id=None, corpus=None, limit=100, mysession=None):
    '''
    Compute the specificity, simple calculus.
    '''
 
    cooccurrences = (mysession.query(NodeNgramNgram)
                    .filter(NodeNgramNgram.node_id==cooc_id)
                    .order_by(NodeNgramNgram.score)
                    .limit(limit)
                    )

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

    node = get_or_create_node(nodetype='Specificity',corpus=corpus, mysession=mysession)

    data = zip(  [node.id for i in range(1,m.shape[0])]
               , [corpus.id for i in range(1,m.shape[0])]
               , m.index.tolist()
               , m.values.tolist()
               )
    mysession.query(NodeNodeNgram).filter(NodeNodeNgram.nodex_id==node.id).delete()
    mysession.commit()

    bulk_insert(NodeNodeNgram, ['nodex_id', 'nodey_id', 'ngram_id', 'score'], [d for d in data])

    return(node.id)
    

def compute_specificity(corpus,limit=100, mysession=None):
    '''
    Computing specificities as NodeNodeNgram.
    All workflow is the following:
        1) Compute the cooc matrix
        2) Compute the specificity score, saving it in database, return its Node
    '''
    
    dbg = DebugTime('Corpus #%d - specificity' % corpus.id)
    
    list_cvalue = get_or_create_node(nodetype='Cvalue', corpus=corpus, mysession=mysession)
    cooc_id = do_cooc(corpus=corpus, cvalue_id=list_cvalue.id,limit=limit, mysession=mysession)

    specificity(cooc_id=cooc_id,corpus=corpus,limit=limit,mysession=mysession)
    dbg.show('specificity')

#corpus=session.query(Node).filter(Node.id==244250).first()
#compute_specificity(corpus)

