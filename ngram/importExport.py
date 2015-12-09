import re
from admin.utils import PrintException

from gargantext_web.db import Node, Ngram, NodeNgram, NodeNodeNgram, NodeNgramNgram
from gargantext_web.db import cache, session, get_or_create_node, bulk_insert

import sqlalchemy as sa
from sqlalchemy.sql import func
from sqlalchemy import desc, asc, or_, and_, Date, cast, select
from sqlalchemy import literal_column
from sqlalchemy.orm import aliased

from ngram.tools import insert_ngrams
from analysis.lists import WeightedList, UnweightedList

from collections import defaultdict

def exportNgramList(node,filename):
    
    # les nodes couvrant les listes
    # -----------------------------
    stop_node  = get_or_create_node(nodetype='StopList', corpus=node)
    miam_node  = get_or_create_node(nodetype='MiamList', corpus=node)
    map_node   = get_or_create_node(nodetype='MapList', corpus=node)
    group_node = get_or_create_node(nodetype='Group', corpus=node)
    
    # listes de ngram_ids correspondantes
    # ------------------------------------
    #~~ contenu: liste des ids [2562,...]
    stop_ngrams_ids  = [stop_ngram.ngram_id for stop_ngram in stop_node.node_node_ngram_collection]
    # idem pour miam et map
    miam_ngrams_ids  = [miam_ng.ngram_id for miam_ng in miam_node.node_node_ngram_collection]
    map_ngrams_ids   = [map_ng.ngram_id for map_ng in map_node.node_node_ngram_collection]
    
    
    # union des listes (est-elle nécessaire ?)
    all_ngrams = set(
              set(stop_ngrams_ids) 
            | set(map_ngrams_ids) 
            | set(miam_ngrams_ids)
            )
    
    
    # pour la group_list on a des couples de ngram_ids
    # -------------------
    # ex: [(3544, 2353), (2787, 4032), ...]
    group_ngrams_id_couples = [(nd_ng_ng.ngramx_id,nd_ng_ng.ngramy_id) for nd_ng_ng in group_node.node_nodengramngram_collection]

    # k couples comme set 
    # --------------------
    # [(a => x) (a => y)] => [a => {x,y}]
    grouped = defaultdict(set)
    
    for ngram in group_ngrams :
        grouped[ngram[0]].add(ngram[1])
        all_ngrams.add(ngram[0])
        all_ngrams.add(ngram[1])
    
    toList  = list()
    
    # pour récupérer les objets Ngram (avec terme)
    # -------------------------------
    # session.query(Ngram).filter(Ngram.id.in_(stop_ngrams_ids)).all()
    
    # in_ => OUTER JOIN préalable ?

    #~ def add_ngram(fromList, toList=toList, grouplist=grouped, all_ngrams=all_ngrams, weight=0):
        #~ for ngram_id in from_list:
            #~ all_ngrams.add(ngram_id)
            #~ if ngram_id in grouplist.keys():
                #~ ngrams.append((ngram_id, grouped[ngram_id], weight))
            #~ else :
                #~ ngram.append((ngram_id, "", weight))
    #~ 
    #~ add_ngrams(stop_ngrams, weight=0)
    #~ add_ngrams(miam_ngrams, weight=1)
    #~ add_ngrams(map_ngrams,  weight=2)

    # to csv
    with open(filename, "w") as f:
        for ngram in ngrams:
            f.write(ngram)


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


