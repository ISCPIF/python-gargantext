import re
from admin.utils import PrintException

from gargantext_web.db import Node, Ngram, NodeNgram,NodeNodeNgram
from gargantext_web.db import cache, session, get_or_create_node, bulk_insert

import sqlalchemy as sa
from sqlalchemy.sql import func
from sqlalchemy import desc, asc, or_, and_, Date, cast, select
from sqlalchemy import literal_column
from sqlalchemy.orm import aliased

from ngram.tools import insert_ngrams
from analysis.lists import WeightedList, UnweightedList

def exportNgramList(node,filename):
    stop_node  = get_or_create_node(nodetype='StopList', corpus=node)
    miam_node  = get_or_create_node(nodetype='MiamList', corpus=node)
    map_node   = get_or_create_node(nodetype='MapList', corpus=node)
    group_node = get_or_create_node(nodetype='Group', corpus=node)
    
    stop_ngrams = session.query(NodeNgram.ngram_id).filter(NodeNgram.node_id==stop_node.id).all()
    miam_ngrams = session.query(NodeNgram.ngram_id).filter(NodeNgram.node_id==miam_node.id).all()
    map_ngrams  = session.query(NodeNgram.ngram_id).filter(NodeNgram.node_id==map_node.id).all()
    group_ngrams= (session.query(NodeNgramNgram.ngramx_id, NodeNgramNgram.ngramy_id)
                          .filter(NodeNgramNgram.node_id==group_node.id)
                          .all()
                          )

    all_ngrams = set()
    grouped = defaultdict(lambda: defaultdict(set))
    toList  = list()

    for ngram in group_ngrams :
        grouped[ngram[0]].add(ngram[1])
        all_ngrams.add(ngram[0])
        all_ngrams.add(ngram[1])

    def add_ngram(fromList, toList=toList, grouplist=grouped, all_ngrams=all_ngrams, weight=0):
        for ngram_id in from_list:
            all_ngrams.add(ngram_id)
            if ngram_id in grouplist.keys():
                ngrams.append((ngram_id, grouped[ngram_id], weight))
            else :
                ngram.append((ngram_id, "", weight))
    
    add_ngrams(stop_ngrams, weight=0)
    add_ngrams(miam_ngrams, weight=1)
    add_ngrams(map_ngrams,  weight=2)

    # to csv
    with open(filename, "w") as f:
        f.write(ngram) for ngram in ngrams


def importNgramList(node,filename):
    '''
    Suppose 
    '''
    with open(filename, "r") as f:
        ngrams_list = f.read().splitlines()
    

    # for row  delete others and 


    stop_words = set(stop_list)
    stop_ids = insert_ngrams([(word, len(word.split(' '))) for word in stop_words])

    stop_node = get_or_create_node(nodetype='StopList', corpus=node)
    
    session.add(stop_node)
    session.commit()
    
    size = len(list(stop_words))

    data = zip(
        [stop_node.id for i in range(0,size)]
        , [stop_ids[word] for word in list(stop_words)]
        , [-1 for i in range(0,size)]
    )
    
    bulk_insert(NodeNgram, ['node_id', 'ngram_id', 'weight'], [d for d in data])


