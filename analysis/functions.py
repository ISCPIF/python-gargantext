from admin.utils import PrintException
from gargantext_web.db import *

from collections import defaultdict
from django.db import connection, transaction

import math
from math import log

import scipy

from gargantext_web.db import get_or_create_node

from analysis.cooccurrences import do_cooc

import pandas as pd
from copy import copy
import numpy as np
import scipy
import networkx as nx
from networkx.readwrite import json_graph
from rest_v1_0.api import JsonHttpResponse

from analysis.louvain import best_partition, generate_dendogram, partition_at_level

from ngram.lists import listIds
from sqlalchemy.orm import aliased

def diag_null(x):
    return x - x * scipy.eye(x.shape[0])


def do_distance(cooc_id, field1=None, field2=None, isMonopartite=True):
    '''
    do_distance :: Int -> (Graph, Partition, {ids}, {weight})
    '''
    #print([n for n in session.query(NodeNgramNgram).filter(NodeNgramNgram.node_id==cooc_id).all()])
    
    matrix = defaultdict(lambda : defaultdict(float))
    ids    = defaultdict(lambda : defaultdict(int))
    labels = dict()
    weight = dict()

    Cooc = aliased(NodeNgramNgram)

    query = session.query(Cooc).filter(Cooc.node_id==cooc_id).all()
    
    for cooc in query:
        matrix[cooc.ngramx_id][cooc.ngramy_id] = cooc.score
        matrix[cooc.ngramy_id][cooc.ngramx_id] = cooc.score

        ids[cooc.ngramx_id] = (field1, cooc.ngramx_id)
        ids[cooc.ngramy_id] = (field2, cooc.ngramy_id)

        weight[cooc.ngramx_id] = weight.get(cooc.ngramx_id, 0) + cooc.score
        weight[cooc.ngramy_id] = weight.get(cooc.ngramy_id, 0) + cooc.score

    x = pd.DataFrame(matrix).fillna(0)
    y = pd.DataFrame(matrix).fillna(0)

    #xo = diag_null(x)
    #y = diag_null(y)

    x = x / x.sum(axis=1)
    y = y / y.sum(axis=0)

    xs = x.sum(axis=1) - x
    ys = x.sum(axis=0) - x

    # top inclus ou exclus
    n = ( xs + ys) / (2 * (x.shape[0] - 1))
    # top generic or specific
    m = ( xs - ys) / (2 * (x.shape[0] - 1))

    n = n.sort(inplace=False)
    m = m.sort(inplace=False)

    nodes_included = 300 #int(round(size/20,0))
    #nodes_excluded = int(round(size/10,0))

    nodes_specific = 300 #int(round(size/10,0))
    #nodes_generic = int(round(size/10,0))

    # TODO use the included score for the node size
    n_index = pd.Index.intersection(x.index, n.index[:nodes_included])
    # Generic:
    #m_index = pd.Index.intersection(x.index, m.index[:nodes_generic])
    # Specific:
    m_index = pd.Index.intersection(x.index, m.index[-nodes_specific:])

    x_index = pd.Index.union(n_index, m_index)
    xx = x[list(x_index)].T[list(x_index)]

    # Removing unconnected nodes
    xxx = xx.values
    threshold = min(xxx.max(axis=1))
    matrix_filtered = np.where(xxx >= threshold, xxx, 0)
    #matrix_filtered = matrix_filtered.resize((90,90))

    G = nx.from_numpy_matrix(np.matrix(matrix_filtered))
    #G = nx.from_numpy_matrix(matrix_filtered, create_using=nx.MultiDiGraph())

    G = nx.relabel_nodes(G, dict(enumerate([ ids[id_][1] for id_ in list(xx.columns)])))
    # Removing too connected nodes (find automatic way to do it)
    #edges_to_remove = [ e for e in G.edges_iter() if

    G.remove_nodes_from(nx.isolates(G))
    # = degree = G.degree()
    #   nodes_to_remove = [n for n in degree if degree[n] <= 1]
    #   G.remove_nodes_from(nodes_to_remove)
    
    partition = best_partition(G.to_undirected())
    print("Density of the graph:", nx.density(G))

    return(G,partition,ids,weight)


def get_cooc(request=None, corpus=None
        , field1='ngrams', field2='ngrams'
        , cooc_id=None, type='node_link', size=1000
        , start=None, end=None
        , apax=1
        ):
    '''
    get_ccoc : to compute the graph.
    '''
    #if session.query(Node).filter(Node.type_id==type_cooc_id, Node.parent_id==corpus_id).first() is None:
    print("Coocurrences do not exist yet, create it.")
    miam_id = get_or_create_node(nodetype='MiamList', corpus=corpus).id
    stop_id = get_or_create_node(nodetype='StopList', corpus=corpus).id
    group_id = get_or_create_node(nodetype='Group', corpus=corpus).id
    
    
    if field1 == field2 == 'ngrams' :
        isMonopartite = True
    else:
        isMonopartite = False

    # data deleted each time
    #cooc_id = get_or_create_node(nodetype='Cooccurrence', corpus=corpus).id
    cooc_id = do_cooc(corpus=corpus, field1=field1, field2=field2
            , miam_id=miam_id, group_id=group_id, stop_id=stop_id, limit=size
            , isMonopartite=isMonopartite
            , apax=apax)
    
    G, partition, ids, weight = do_distance(cooc_id, field1=field1, field2=field2, isMonopartite=isMonopartite)

    if type == "node_link":
        for node_id in G.nodes():
            try:
                #node,type(labels[node])
                G.node[node_id]['pk'] = ids[node_id][1]
                the_label = session.query(Ngram.terms).filter(Ngram.id==node_id).first()
                the_label = ", ".join(the_label)
                # TODO the query below is not optimized (do it do_distance).
                G.node[node_id]['label']   = the_label
                
                G.node[node_id]['size']    = weight[node_id]
                G.node[node_id]['type']    = ids[node_id][0].replace("ngrams","terms")
                G.node[node_id]['attributes'] = { "clust_default": partition[node_id]} # new format
                # G.add_edge(node, "cluster " + str(partition[node]), weight=3)
            except Exception as error:
                pass #PrintException()
                #print("error01: ",error)

        data = json_graph.node_link_data(G)

        links = []
        i=1
        for e in G.edges_iter():
            s = e[0]
            t = e[1]
            info = { "id":i , "source":ids[s][1] , "target":ids[t][1]}
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
    elif type == 'bestpartition':
        return(partition)

    #    data = json_graph.node_link_data(G, attrs={\
    #            'source':'source',\
    #            'target':'target',\
    #            'weight':'weight',\
    #            #'label':'label',\
    #            #'color':'color',\
    #            'id':'id',})
    #print(data)
    return(data)

