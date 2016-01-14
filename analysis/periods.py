
from collections import defaultdict

from gargantext_web.db import get_or_create_node, get_session, Node, NodeHyperdata, Hyperdata, Ngram

import pandas as pd
import numpy as np
import scipy.spatial.distance as distance

from sqlalchemy.sql import func
from sqlalchemy import desc, asc, or_, and_, Date, cast, select
from sqlalchemy import literal_column
from sqlalchemy.orm import aliased

from analysis.distance import do_distance
from analysis.cooccurrences import do_cooc


# TFIDF ngrams / period
def periods(corpus, start=None, end=None):
    '''
    data
    periods :: Corpus -> [Periods]
    
    # compute TFIDF matrix 
    # a = np.asarray([1,2,3])
    # b = np.asarray([1,2,4])

    # distance.cosine(a,b)
    # search for min and split
    '''
    session = get_session()

    Doc    = aliased(Node)
    Corpus = aliased(Node)

    query = (session
            .query(NodeHyperdata.value_datetime)
            .join(Doc, Doc.id == NodeHyperdata.node_id)
            .join(Corpus, Corpus.id == Doc.parent_id)
            .join(Hyperdata, Hyperdata.id == NodeHyperdata.hyperdata_id)
            .filter(Doc.type_id == cache.NodeType['Document'].id)
            .filter(Corpus.id == corpus.id)
            .filter(Hyperdata.name == 'publication_date')
            )
    
    first = query.order_by(asc(NodeHyperdata.value_datetime)).first()[0]
    last  = query.order_by(desc(NodeHyperdata.value_datetime)).first()[0]

    duration = last - first
    if duration.days > 365 * 3 :
        print("OK")

    miam_id = get_or_create_node(nodetype='MiamList', corpus=corpus).id

    result_list = list()
    for t in times:
        for ngram in miam_list:
            result_list.add(temporal_tfidf(ngram, time))
    
    session.remove()

def tfidf_temporal(corpus, start=None, end=None):
    pass

def jacquard(period1, period2):
    '''
    type Start :: Date
    type End   :: Date

    type Period  :: (Start, End)
    type Periods :: [Period]

    '''
    period1 = ['start1', 'end1']
    period2 = ['start2', 'end2']

    periods = [period1, period2]

    nodes = [cooc(corpus=corpus_id, start=period[0], end=period[1]) for period in periods]
    partitions = [get_cooc(cooc_id=node_id, type='bestpartition') for node_id in nodes]

    for x in nodeCom.items():
        comNode[x[1]] = comNode.get(x[1], set()).union({x[0]})

def get_partition(corpus, start=None, end=None, distance=distance):
    session = get_session()
    
    miam_id = get_or_create_node(corpus=corpus, nodetype='MapList', session=session).id
    print("get Partition %s - %s" % (start, end))
    cooc_id = do_cooc(corpus=corpus
            , start=start
            , end=end
            , miam_id = miam_id
            )

    G, partition, ids, weight = do_distance(cooc_id
                                    , field1="ngrams"
                                    , field2="ngrams"
                                    , isMonopartite=True
                                    , distance=distance)
    return(partition, weight)
    session.remove()

def phylo_clusters(corpus, years):
    '''
    corpus :: Node Corpus
    years  :: [Year]
    '''
    session = get_session()

    clusters     = dict()
    nodes_weight = dict()
    
    periods_start_end = [
              ('2000-01-01', '2010-12-31')
            , ('2011-01-01', '2012-12-31')
            , ('2013-01-01', '2015-12-31')
            ]
    
    periods = list()
    for period in periods_start_end:
        periods.append(' '.join(p for p in period))
    print(periods)
    periods_index = [ z for z in zip (periods[:-1], periods[1:])]
    print(periods_index)
    
    for period in periods_start_end:
        #start,end = period
        index = ' '.join([str(p) for p in list(period)]) 
        clusters[index], nodes_weight[index] = get_partition( corpus
                , start = str(period[0])
                , end   = str(period[1])
                , distance='distributional')

    nodes = set()
    for period in nodes_weight.keys():
        for node in nodes_weight[period].keys():
            nodes.add(node)


    id_terms = session.query(Ngram.id, Ngram.terms).filter(Ngram.id.in_(nodes)).all()
    id_terms_dict = dict()
    for id_term in id_terms:
        id_terms_dict[id_term[0]] = id_term[1]

    year_com_node = defaultdict(lambda: defaultdict(set))

    for period in clusters.keys():
        for node, com in clusters[period].items():
            year_com_node[period][com].add(node)

    proximity_dict = defaultdict(
                        lambda: defaultdict(
                            lambda: defaultdict(
                                lambda: defaultdict( float
                                                   )
                                               )
                                           )
                                )

    def t1_t2(proximity_dict, t1_t2):
        t1,t2 = t1_t2
        for com1 in year_com_node[t1].keys():
            for com2 in year_com_node[t2].keys():
                
                set_1 = year_com_node[t1][com1]
                set_2 = year_com_node[t2][com2]
                
                intersection = set_1.intersection(set_2)
                union        = set_1.union(set_2)

                proximity_dict[t1][t2][com1][com2] = len(intersection) / len(union)
    
    for period in periods_index:
        t1_t2(proximity_dict, period)
    
    data = list()
    data_dict = dict()

    for y1 in proximity_dict.keys():
        
        for y2 in proximity_dict[y1].keys():
            
            for c1 in proximity_dict[y1][y2].keys():
                
                for c2 in proximity_dict[y1][y2][c1].keys():
                    
                    score = proximity_dict[y1][y2][c1][c2]
                    if score > 0.05:
                        #print(y1,y2,c1,c2,score)
                        
                        list_node1 = list()
                        for node in year_com_node[y1][c1]:
                            list_node1.append((node, nodes_weight[y1][node]))
                        list_node1 = sorted(list_node1, key=lambda x: x[1], reverse=True)
                        
                        list_node2 = list()
                        for node in year_com_node[y2][c2]:
                            list_node2.append((node, nodes_weight[y2][node]))
                        list_node2 = sorted(list_node2, key=lambda x: x[1], reverse=True)
                        
                        flow = list()
                        from_data = [id_terms_dict[x[0]] for x in list_node1[:2]]
                        from_data.append(str(y1))
                        flow.append(','.join(from_data))

                        to_data = [id_terms_dict[x[0]] for x in list_node2[:2]]
                        to_data.append(str(y2))
                        flow.append(','.join(to_data))

                        flow.append(round(score*100))

                        data.append(flow)

    return(data)
    session.remove()

