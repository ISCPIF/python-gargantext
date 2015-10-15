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

from analysis.louvain import best_partition, generate_dendogram, partition_at_level

from ngram.lists import listIds


def diag_null(x):
    return x - x * scipy.eye(x.shape[0])


size = 1000


def get_cooc(request=None, corpus=None, cooc_id=None, type='node_link', size=size):
    '''
    get_ccoc : to compute the graph.
    '''
    matrix = defaultdict(lambda : defaultdict(float))
    ids    = dict()
    labels = dict()
    weight = dict()

    #if session.query(Node).filter(Node.type_id==type_cooc_id, Node.parent_id==corpus_id).first() is None:
    print("Coocurrences do not exist yet, create it.")
    miam_id = get_or_create_node(nodetype='MiamList', corpus=corpus).id
    stop_id = get_or_create_node(nodetype='StopList', corpus=corpus).id
    group_id = get_or_create_node(nodetype='Group', corpus=corpus).id
    cooc_id = get_or_create_node(nodetype='Cooccurrence', corpus=corpus).id
    
    # data deleted each time
    session.query(NodeNgramNgram).filter(NodeNgramNgram.node_id==cooc_id).delete()
    cooc_id = cooc(corpus=corpus, miam_id=miam_id, group_id=group_id, stop_id=stop_id, limit=size)

    #print([n for n in session.query(NodeNgramNgram).filter(NodeNgramNgram.node_id==cooc_id).all()])
    for cooccurrence in session.query(NodeNgramNgram).filter(NodeNgramNgram.node_id==cooc_id).all():
        #print(cooccurrence)
        # print(cooccurrence.ngramx.terms," <=> ",cooccurrence.ngramy.terms,"\t",cooccurrence.score)
        # TODO clean this part, unuseful
        labels[cooccurrence.ngramx_id] = cooccurrence.ngramx_id #session.query(Ngram.id).filter(Ngram.id == cooccurrence.ngramx_id).first()[0]
        labels[cooccurrence.ngramy_id] = cooccurrence.ngramy_id #session.query(Ngram.id).filter(Ngram.id == cooccurrence.ngramy_id).first()[0]

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

    G = nx.from_numpy_matrix(np.matrix(matrix_filtered))
    #G = nx.from_numpy_matrix(matrix_filtered, create_using=nx.MultiDiGraph())

    G = nx.relabel_nodes(G, dict(enumerate([ labels[label] for label in list(xx.columns)])))
    # Removing too connected nodes (find automatic way to do it)
    #edges_to_remove = [ e for e in G.edges_iter() if

    degree = G.degree()
    nodes_to_remove = [n for n in degree if degree[n] <= 1]
    G.remove_nodes_from(nodes_to_remove)
    uG = G.to_undirected()
    partition = best_partition(uG)
    print(partition)
    print("Density of the graph:", nx.density(G))


    if type == "node_link":

        for node in G.nodes():
            try:
                #node,type(labels[node])
                G.node[node]['pk'] = ids[node]
                G.node[node]['label']   = session.query(Ngram.terms).filter(Ngram.id==node).first()
                G.node[node]['size']    = weight[ids[node]]
                G.node[node]['group']   = partition[node]
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

