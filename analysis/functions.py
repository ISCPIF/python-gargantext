from admin.utils import PrintException
from gargantext_web.db import *

from collections import defaultdict
from django.db import connection, transaction

import math
from math import log

import scipy

def diag_null(x):
    return x - x * scipy.eye(x.shape[0])

def create_blacklist(user, corpus):
    pass

def create_synonymes(user, corpus):
    pass
    

size = 1000 

def create_whitelist(user, corpus_id, size=size):
    cursor = connection.cursor()
    
    whitelist_type_id = cache.NodeType['WhiteList'].id
    blacklist_type_id = cache.NodeType['BlackList'].id
    type_document_id  = cache.NodeType['Document'].id

    white_list = Node(name='WhiteList Corpus ' + str(corpus_id), user_id=user.id, parent_id=corpus_id, type_id=whitelist_type_id)
    black_list = Node(name='BlackList Corpus ' + str(corpus_id), user_id=user.id, parent_id=corpus_id, type_id=blacklist_type_id)
    
    session.add(white_list)
    session.add(black_list)
    
    session.commit()
    # delete avant pour éviter les doublons
    #    try:
    #        Node_Ngram.objects.filter(node=white_list).all().delete()
    #    except:
    #        print('First time we compute cooc')
    #
    query_whitelist = """
        INSERT INTO node_node_ngram (node_id, ngram_id, weight)
        SELECT
            %d,
            ngX.id,
            COUNT(*) AS occurrences
        FROM
            node_node AS n
        INNER JOIN
            node_node_ngram AS nngX ON nngX.node_id = n.id
        INNER JOIN
            node_ngram AS ngX ON ngX.id = nngX.ngram_id
        WHERE
            n.parent_id = %d
        AND
            n.type_id = %d
        AND
        ngX.n >= 2
        AND
        ngX.n <= 3


        GROUP BY
            ngX.id
        Having
            COUNT(*) >= 3
        ORDER BY
            occurrences DESC
        LIMIT
            %d
        ;
    """  % (white_list.id, int(corpus_id), int(type_document_id), size)
    # print("PRINTING QYERY OF WHITELIST:")
    # print(query_whitelist)
    cursor.execute(query_whitelist)

    return white_list

#def create_cooc(user, corpus, whitelist, blacklist, synonymes):
def create_cooc(user=None, corpus_id=None, whitelist=None, size=size, year_start=None, year_end=None):
    cursor = connection.cursor()

    cooc_type_id  = cache.NodeType['Cooccurrence'].id

    # pour les tests on supprime les cooc
    #session.Node.objects.filter(type=cooc_type, parent=corpus).delete()

    cooc = Node(user_id=user.id,\
                           parent_id=corpus_id,\
                           type_id=cooc_type_id,\
                           name="Cooccurrences corpus " + str(corpus_id))

    session.add(cooc)
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
        node_node_ngram AS whitelistX ON whitelistX.ngram_id = nngX.ngram_id -- list of ngrams contained in the whitelist and in the node
    INNER JOIN
        node_ngram AS ngX ON ngX.id = whitelistX.ngram_id -- ngrams which are in both
        
    INNER JOIN
        node_node_ngram AS nngY ON nngY.node_id = n.id
    INNER JOIN
        node_node_ngram AS whitelistY ON whitelistY.ngram_id = nngY.ngram_id
    INNER JOIN
        node_ngram AS ngY ON ngY.id = whitelistY.ngram_id
        
    WHERE
        n.parent_id = %s
    AND
        whitelistX.node_id = %s
    AND
        whitelistY.node_id = %s
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
    """ % (cooc.id, corpus_id, whitelist.id, whitelist.id, size)

    # print(query_cooc)
    cursor.execute(query_cooc)
    return cooc.id

def get_cooc(request=None, corpus_id=None, cooc_id=None, type='node_link', size=size):
    import pandas as pd
    from copy import copy
    import numpy as np
    import scipy
    import networkx as nx
    from networkx.readwrite import json_graph
    from gargantext_web.api import JsonHttpResponse
    
    from analysis.louvain import best_partition
    
    #print(corpus_id, cooc_id)

    try:
        matrix = defaultdict(lambda : defaultdict(float))
        ids    = dict()
        labels = dict()
        weight = dict()

        type_cooc_id = cache.NodeType['Cooccurrence'].id

        if session.query(Node).filter(Node.type_id==type_cooc_id, Node.parent_id==corpus_id).first() is None:
            print("Coocurrences do not exist yet, create it.")
            whitelist = create_whitelist(request.user, corpus_id=corpus_id, size=size)
            cooccurrence_node_id = create_cooc(user=request.user, corpus_id=corpus_id, whitelist=whitelist, size=size)
        else:
            cooccurrence_node_id = session.query(Node.id).filter(Node.type_id==type_cooc_id, Node.parent_id==corpus_id).first()
        


        for cooccurrence in session.query(NodeNgramNgram).filter(NodeNgramNgram.node_id==cooccurrence_node_id).all():
            # print(cooccurrence.ngramx.terms," <=> ",cooccurrence.ngramy.terms,"\t",cooccurrence.score)
            labels[cooccurrence.ngramx_id] = session.query(Ngram.terms).filter(Ngram.id == cooccurrence.ngramx_id).first()[0]
            labels[cooccurrence.ngramy_id] = session.query(Ngram.terms).filter(Ngram.id == cooccurrence.ngramy_id).first()[0]

            matrix[cooccurrence.ngramx_id][cooccurrence.ngramy_id] = cooccurrence.score
            matrix[cooccurrence.ngramy_id][cooccurrence.ngramx_id] = cooccurrence.score

            ids[labels[cooccurrence.ngramx_id]] = cooccurrence.ngramx_id
            ids[labels[cooccurrence.ngramy_id]] = cooccurrence.ngramy_id

            weight[cooccurrence.ngramx_id] = weight.get(cooccurrence.ngramx_id, 0) + cooccurrence.score
            weight[cooccurrence.ngramy_id] = weight.get(cooccurrence.ngramy_id, 0) + cooccurrence.score


        x = pd.DataFrame(matrix).fillna(0)
        y = pd.DataFrame(matrix).fillna(0)
#    x = copy(df.values)
#    y = copy(df.values)
        #xo = diag_null(x)
        #y = diag_null(y)
        
        x = x / x.sum(axis=1)
        y = y / y.sum(axis=0)
        #print(x)

        xs = x.sum(axis=1) - x
        ys = x.sum(axis=0) - x
    
        # top inclus
        #n = ( xs + ys) / (2 * (x.shape[0] -1))
        # top specific ?
        m = ( xs - ys) / (2 * (x.shape[0] -1))
        # top generic ?
        #m = ( ys - ss) / (2 * (x.shape[0] -1))
        #m = pd.DataFrame.abs(m)
        
        #n = n.sort(inplace=False)
        m = m.sort(inplace=False)
        
        matrix_size = int(round(size/2,0))

        #n_index = pd.Index.intersection(x.index, n.index[-matrix_size:])
        m_index = pd.Index.intersection(x.index, m.index[-matrix_size:])
        
        x_index = m_index# pd.Index.union(n_index, m_index)
        xx = x[list(x_index)].T[list(x_index)]

        # import pprint
        # pprint.pprint(ids)

        # Removing unconnected nodes
        xxx = xx.values
        threshold = min(xxx.max(axis=1))
        matrix_filtered = np.where(xxx > threshold, xxx, 0)
        
        #matrix_filtered = matrix_filtered.resize((90,90))
    except:
        PrintException()
    
    try:
        G = nx.from_numpy_matrix(matrix_filtered)
        G = nx.relabel_nodes(G, dict(enumerate([ labels[label] for label in list(xx.columns)])))
        
        #print(G)
        #G = nx.relabel_nodes(G, dict(enumerate(df.columns)))
        # Removing too connected nodes (find automatic way to do it)
        #    outdeg = G.degree()
        #    to_remove = [n for n in outdeg if outdeg[n] >= 10]
        #    G.remove_nodes_from(to_remove)

        partition = best_partition(G)
    except:
        PrintException()
    

    if type == "node_link":

        for node in G.nodes():
            try:
                #node,type(labels[node])
                G.node[node]['pk'] = ids[node]
                G.node[node]['label']   = node
                # G.node[node]['pk']      = ids[str(node)]
                G.node[node]['size']    = weight[ids[node]]
                G.node[node]['group']   = partition[node]
                # G.add_edge(node, "cluster " + str(partition[node]), weight=3)
            except Exception as error:
                print("error01: ",error)
        
        data = json_graph.node_link_data(G)

        links = []
        i=1
        for e in G.edges_iter():
            s = e[0]
            t = e[1]
            info = { "id":i , "source":ids[s] , "target":ids[t]}
            # print(info)
            links.append(info)
            i+=1
        # print(data)
        data["links"] = []
        data["links"] = links
    
    elif type == "adjacency":
        for node in G.nodes():
            try:
                #node,type(labels[node])
                #G.node[node]['label']   = node
                G.node[node]['name']    = node
                #G.node[node]['size']    = weight[node]
                G.node[node]['group']   = partition[node]
                #G.add_edge(node, partition[node], weight=3)
            except Exception as error:
                print("error02: ",error)
        data = json_graph.node_link_data(G)
     

    #    data = json_graph.node_link_data(G, attrs={\
    #            'source':'source',\
    #            'target':'target',\
    #            'weight':'weight',\
    #            #'label':'label',\
    #            #'color':'color',\
    #            'id':'id',})
    #print(data)
    return data

