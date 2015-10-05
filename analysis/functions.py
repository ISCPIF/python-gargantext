from admin.utils import PrintException
from gargantext_web.db import *

from collections import defaultdict
from django.db import connection, transaction

import math
from math import log

import scipy

from gargantext_web.db import get_or_create_node

from analysis.cooccurrences import cooc

import pandas as pd
from copy import copy
import numpy as np
import scipy
import networkx as nx
from networkx.readwrite import json_graph
from rest_v1_0.api import JsonHttpResponse

from analysis.louvain import best_partition
from ngram.lists import listIds


def diag_null(x):
    return x - x * scipy.eye(x.shape[0])

def create_blacklist(user, corpus):
    pass

def create_synonymes(user, corpus):
    pass


size = 1000

def create_whitelist(user, corpus_id, size=size, count_min=2, miam_id=None):
    if miam_id is None:
        PrintException()

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
        INNER JOIN
            node_node_ngram AS miam ON ngX.id = miam.ngram_id
        WHERE
            n.parent_id = %d
        AND
            n.type_id = %d
        AND
            miam.node_id = %d
        AND
        ngX.n >= 2
        AND
        ngX.n <= 3


        GROUP BY
            ngX.id
        Having
            COUNT(*) >= %d
        ORDER BY
            occurrences DESC
        LIMIT
            %d
        ;
    """  % (white_list.id, int(corpus_id), int(type_document_id), int(miam_id), count_min, size)

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

def get_cooc(request=None, corpus=None, cooc_id=None, type='node_link', size=size):

    matrix = defaultdict(lambda : defaultdict(float))
    ids    = dict()
    labels = dict()
    weight = dict()

    #if session.query(Node).filter(Node.type_id==type_cooc_id, Node.parent_id==corpus_id).first() is None:
    print("Coocurrences do not exist yet, create it.")
    miam_id = get_or_create_node(nodetype='MiamList', corpus=corpus).id
    stop_id = get_or_create_node(nodetype='StopList', corpus=corpus).id
    group_id = get_or_create_node(nodetype='Group', corpus=corpus).id
    
    #cooc_id = cooc(corpus=corpus, miam_id=miam_id, stop_id=stop_id, limit=size)
    cooc_id = cooc(corpus=corpus, miam_id=miam_id, group_id=group_id, stop_id=stop_id, limit=size)
    #cooc_id = cooc(corpus=corpus, miam_id=miam_id, limit=size)

    print([n for n in session.query(NodeNgramNgram).filter(NodeNgramNgram.node_id==cooc_id).all()])
    for cooccurrence in session.query(NodeNgramNgram).filter(NodeNgramNgram.node_id==cooc_id).all():
        #print(cooccurrence)
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

    #xo = diag_null(x)
    #y = diag_null(y)

    x = x / x.sum(axis=1)
    y = y / y.sum(axis=0)
    #print(x)

    xs = x.sum(axis=1) - x
    ys = x.sum(axis=0) - x

    # top inclus ou exclus
    n = ( xs + ys) / (2 * (x.shape[0] - 1))
    # top generic or specific
    m = ( xs - ys) / (2 * (x.shape[0] - 1))

    n = n.sort(inplace=False)
    m = m.sort(inplace=False)

    #print(n)
    #print(m)

    nodes_included = 300 #int(round(size/20,0))
    #nodes_excluded = int(round(size/10,0))

    nodes_specific = 300 #int(round(size/10,0))
    #nodes_generic = int(round(size/10,0))

    # TODO user the included score for the node size
    n_index = pd.Index.intersection(x.index, n.index[:nodes_included])
    # Generic:
    #m_index = pd.Index.intersection(x.index, m.index[:nodes_generic])
    # Specific:
    m_index = pd.Index.intersection(x.index, m.index[-nodes_specific:])

    x_index = pd.Index.union(n_index, m_index)
    xx = x[list(x_index)].T[list(x_index)]

    # import pprint
    # pprint.pprint(ids)

    # Removing unconnected nodes
    xxx = xx.values
    threshold = min(xxx.max(axis=1))
    matrix_filtered = np.where(xxx >= threshold, xxx, 0)
    #matrix_filtered = matrix_filtered.resize((90,90))

    try:
        G = nx.from_numpy_matrix(np.matrix(matrix_filtered))
        #G = nx.from_numpy_matrix(matrix_filtered, create_using=nx.MultiDiGraph())

        G = nx.relabel_nodes(G, dict(enumerate([ labels[label] for label in list(xx.columns)])))
        # Removing too connected nodes (find automatic way to do it)
        #edges_to_remove = [ e for e in G.edges_iter() if

        degree = G.degree()
        nodes_to_remove = [n for n in degree if degree[n] ==0]
        G.remove_nodes_from(nodes_to_remove)
        uG = G.to_undirected()
        partition = best_partition(uG)
    except:
        print("-" * 30)
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
                pass#PrintException()
                #print("error01: ",error)

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

