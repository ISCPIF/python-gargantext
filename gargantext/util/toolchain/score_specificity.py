from gargantext.util.db import *
from gargantext.util.db_cache import *
from gargantext.constants import *

from gargantext.util.analysis.cooccurrences import do_cooc

from gargantext.models.ngrams import Ngram, NodeNgram,\
        NodeNgramNgram, NodeNodeNgram

import numpy as np
import pandas as pd
from collections import defaultdict
from sqlalchemy import desc, asc, or_, and_, Date, cast, select

def specificity(cooc_id=None, corpus=None, limit=100, session=None):
    '''
    Compute the specificity, simple calculus.
    '''
 
    cooccurrences = (session.query(NodeNgramNgram)
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

    #node = get_or_create_node(nodetype='Specificity',corpus=corpus)

    node = session.query(Node).filter(
        Node.parent_id==corpus_id,
        Node.typename == "SPECIFICITY"
        ).first()

    if node == None:
        corpus = cache.Node[corpus_id]
        user_id = corpus.user_id
        node = Node(name="SPECIFICITY", parent_id=corpus_id, user_id=user_id, typename="SPECIFICITY")
        session.add(node)
        session.commit()


    data = zip(  [node.id for i in range(1,m.shape[0])]
               , [corpus.id for i in range(1,m.shape[0])]
               , m.index.tolist()
               , m.values.tolist()
               )
    session.query(NodeNodeNgram).filter(NodeNodeNgram.nodex_id==node.id).delete()
    session.commit()

    bulk_insert(NodeNodeNgram, ['nodex_id', 'nodey_id', 'ngram_id', 'score'], [d for d in data])

    return(node.id)
    

def compute_specificity(corpus,limit=100, session=None):
    '''
    Computing specificities as NodeNodeNgram.
    All workflow is the following:
        1) Compute the cooc matrix
        2) Compute the specificity score, saving it in database, return its Node
    '''
    
    #dbg = DebugTime('Corpus #%d - specificity' % corpus.id)
    
    #list_cvalue = get_or_create_node(nodetype='Cvalue', corpus=corpus)
    cooc_id = do_cooc(corpus=corpus, cvalue_id=list_cvalue.id,limit=limit)

    specificity(cooc_id=cooc_id,corpus=corpus,limit=limit,session=session)
    #dbg.show('specificity')

#corpus=session.query(Node).filter(Node.id==244250).first()
#compute_specificity(corpus)

