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

    nodes_included = 500 #int(round(size/20,0))
    #nodes_excluded = int(round(size/10,0))

    nodes_specific = 500 #int(round(size/10,0))
    #nodes_generic = int(round(size/10,0))

    # TODO use the included score for the node size
    n_index = pd.Index.intersection(x.index, n.index[:nodes_included])
    # Generic:
    #m_index = pd.Index.intersection(x.index, m.index[:nodes_generic])
    # Specific:
    m_index = pd.Index.intersection(x.index, m.index[-nodes_specific:])
    #m_index = pd.Index.intersection(x.index, n.index[:nodes_included])

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

    #   nodes_to_remove = [n for n in degree if degree[n] <= 1]
    #   G.remove_nodes_from(nodes_to_remove)
    

    def getWeight(item):
        return item[1]
    
    node_degree = sorted(G.degree().items(), key=getWeight, reverse=True)
    print(node_degree)
    nodes_too_connected = [n[0] for n in node_degree[0:(round(len(node_degree)/5))]]

    for n in nodes_too_connected:
        n_edges = list()
        for v in nx.neighbors(G,n):
            n_edges.append(((n, v), G[n][v]['weight']))

        n_edges_sorted = sorted(n_edges, key=getWeight, reverse=True)
        #G.remove_edges_from([ e[0] for e in n_edges_sorted[round(len(n_edges_sorted)/2):]])
        G.remove_edges_from([ e[0] for e in n_edges_sorted[(round(len(nx.neighbors(G,n))/3)):]])

    G.remove_nodes_from(nx.isolates(G))
    partition = best_partition(G.to_undirected())

    return(G,partition,ids,weight)

def get_cooc(request=None, corpus=None
        , field1='ngrams', field2='ngrams'
        , cooc_id=None, type='node_link', size=1000
        , start=None, end=None
        , hapax=1
        ):
    '''
    get_ccoc : to compute the graph.
    '''
    data = {}
    #if session.query(Node).filter(Node.type_id==type_cooc_id, Node.parent_id==corpus_id).first() is None:
    print("Cooccurrences do not exist yet, creating it.")
    miam_id = get_or_create_node(nodetype='MapList', corpus=corpus).id
    stop_id = get_or_create_node(nodetype='StopList', corpus=corpus).id
    group_id = get_or_create_node(nodetype='Group', corpus=corpus).id
    
    SamuelFlag = False
    # if field1 == field2 == 'ngrams' :
    #     isMonopartite = True
    #     SamuelFlag = True
    # else:
    #     isMonopartite = False
    isMonopartite = True # Always. So, calcule the graph B and from these B-nodes, build the graph-A
    # data deleted each time
    #cooc_id = get_or_create_node(nodetype='Cooccurrence', corpus=corpus).id
    cooc_id = do_cooc(corpus=corpus, field1="ngrams", field2="ngrams"
            , miam_id=miam_id, group_id=group_id, stop_id=stop_id, limit=size
            , isMonopartite=True, start=start , end=end , hapax=hapax)
    
    G, partition, ids, weight = do_distance(cooc_id, field1="ngrams", field2="ngrams", isMonopartite=True)

    if type == "node_link":
        nodesB_dict = {}
        for node_id in G.nodes():
            try:
                #node,type(labels[node])
                G.node[node_id]['pk'] = ids[node_id][1]
                nodesB_dict [ ids[node_id][1] ] = True
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

        B = json_graph.node_link_data(G)

        links = []
        i=1
        for e in G.edges_iter():
            s = e[0]
            t = e[1]
            info = { 
                "s": ids[s][1] , 
                "t": ids[t][1] ,
                "w": G[ids[s][1]][ids[t][1]]["weight"]
            }
            # print(info)
            links.append(info)
            i+=1
            # print(B)
        B["links"] = []
        B["links"] = links

        if field1 == field2 == 'ngrams' :
            data["nodes"] = B["nodes"]
            data["links"] = B["links"]
        else:
            A = get_graphA( "journal" , nodesB_dict , B["links"] , corpus )
            print("#nodesA:",len(A["nodes"]))
            print("#linksAA + #linksAB:",len(A["links"]))
            print("#nodesB:",len(B["nodes"]))
            print("#linksBB:",len(B["links"]))
            data["nodes"] = A["nodes"] + B["nodes"]
            data["links"] = A["links"] + B["links"]
            print("  total nodes :",len(data["nodes"]))
            print("  total links :",len(data["links"]))
            print("")

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

    return(data)

def get_graphA( nodeA_type , NodesB , links , corpus ):
    from analysis.InterUnion import Utils
    print(" = = = == = = = ")
    print("In get_graphA(), corpus id:",corpus.id)

    nodeA_type_id = cache.Hyperdata[nodeA_type].id
    threshold_cotainf = 0.02
    max_nodeid = -1
    for nodeid in NodesB:
    	if nodeid > max_nodeid:
    		max_nodeid = nodeid

    # = = = = [ 01. Getting ALL documents of the Corpus c ] = = = =  #
    Docs = {}
    document_type_id = cache.NodeType['Document'].id
    sql_query = 'select id from node_node where parent_id='+str(corpus.id)+' and type_id='+str(document_type_id)
    cursor = connection.cursor()
    cursor.execute(sql_query)
    results = cursor.fetchall()
    for i in results:
        Docs[i[0]] = True
    print("docs:",len(Docs.keys()))
    # = = = = [ / 01. Getting ALL documents of the Corpus c ] = = = =  #


    # = = = = [ 02. Getting ALL Documents related with Ngrams of the carte semantic  ] = = = =  #
    sql_query = 'select nodey_id,ngram_id from node_nodenodengram where ngram_id IN (' + ','.join(map(str, NodesB.keys())) + ")"
    cursor = connection.cursor()
    cursor.execute(sql_query)
    results = cursor.fetchall()
    # = = = = [ / 02. Getting ALL Documents related with Ngrams of the carte semantic  ] = = = =  #


    # = = = = [ 03. Now we limit the retrieved Documents(step 02) to those belonging to the Corpus c ] = = = = ]
    Docs_and_ = {
        "nodesA":{},
        "nodesB":{}
    }
    NodesB_and_Docs = {}
    for i in results:
        doc_id = i[0]
        ngram_id = i[1]
        if ngram_id in NodesB and doc_id in Docs:
            if doc_id not in Docs_and_["nodesB"]:
                Docs_and_["nodesB"][doc_id] = []
            Docs_and_["nodesB"][doc_id].append( ngram_id )
            if ngram_id not in NodesB_and_Docs:
                NodesB_and_Docs[ngram_id] = []
            NodesB_and_Docs[ngram_id].append( doc_id )
    # = = = = [ / 03. Now we limit the retrieved Documents(step 02) to those belonging to the Corpus c ] = = = = ]

    # # = = = = [ Getting Authors ] = = = = ]
    # Authors = {}
    # sql_query = 'select node_id,value_string from node_node_hyperdata where node_id IN (' + ','.join(map(str, Docs_and_["nodesB"].keys())) + ")"+' and hyperdata_id=10'# 10 -> authors
    # cursor = connection.cursor()
    # cursor.execute(sql_query)
    # results = cursor.fetchall()
    # for i in results:
    #     doc_id = i[0]
    #     authors = i[1].split(",")
    #     for a in authors:
    #         if a not in Authors:
    #             Authors[a] = 0
    #         Authors[a] += 1
    # print("")
    # print("#authors:")
    # import pprint
    # pprint.pprint(Authors)
    # print("")
    # # = = = = [ / Getting Authors ] = = = = ]


    # = = = = [ 04. Getting A-elems and making the dictionaries] = = = = ]
    sql_query = 'select node_id,value_string from node_node_hyperdata where node_id IN (' + \
            ','.join(map(str, Docs_and_["nodesB"].keys())) + ")"+' and hyperdata_id='+str(nodeA_type_id)
    cursor = connection.cursor()
    cursor.execute(sql_query)
    results = cursor.fetchall()

    A_Freq = {}
    A_int2str = {}
    A_str2int = {}
    counter = max_nodeid+1
    for i in results:
        doc_id = i[0]
        a = i[1]
        if a not in A_str2int:
            A_str2int[ a ] = counter
            A_int2str[counter] = a
            counter += 1
    for i in results:
        doc_id = i[0]
        a = A_str2int[i[1]]
        Docs_and_["nodesA"][doc_id] = a
        if a not in A_Freq:
            A_Freq[ a ] = 0
        A_Freq[ a ] += 1
    # = = = = [ / 04. Getting A-elems and making the dictionaries ] = = = = ]


    # = = = = [ Filling graph-A ] = = = = ]
    Graph_A = Utils()
    for i in NodesB_and_Docs:
        ngram = i
        docs = NodesB_and_Docs[i]
        k_A_clique = {}
        for doc in docs:
            k_A = Docs_and_["nodesA"][doc]
            k_A_clique[k_A] = True
        if len(k_A_clique.keys())>1:
            Graph_A.addCompleteSubGraph( k_A_clique.keys() )
    # = = = = [ / Filling graph-A ] = = = = ]


    # = = = = [ graph-A to JSON ] = = = = ]
    A = Graph_A.G
    for node_id in A.nodes():
        A.node[node_id]['label']   = A_int2str[node_id]
        A.node[node_id]['size']    = A_Freq[node_id]
        A.node[node_id]['type']    = nodeA_type
        A.node[node_id]['attributes'] = { "clust_default": 1 }

    A_links = []
    min_weight = 999999
    max_weight = -1
    Weights_Dist = {}
    for e in A.edges_iter():
        s = e[0]
        t = e[1]
        w = A[s][t]["weight"]
        if w not in Weights_Dist:
            Weights_Dist[ w ] = { "freq": 0 , "deleted":0 }
        Weights_Dist[ w ]["freq"] += 1
        if min_weight > w:
            min_weight = w
        if max_weight < w:
            max_weight = w

    edges2remove = []
    for e in A.edges_iter():
        s = e[0]
        t = e[1]
        w = A[s][t]["weight"]
        if Weights_Dist [ w ]["freq"] < ( len(A)*3 ): # weight-threshold
            info = { 
                "s":s , 
                "t":t ,
                "w": w / max_weight # normalization
            }
            A_links.append(info)
        else:
            # if Weights_Dist [ w ]["deleted"] < round(Weights_Dist [ w ]["freq"]*0.95):
            atuple = (s,t)
            edges2remove.append(atuple)
            Weights_Dist [ w ]["deleted"] += 1

    A.remove_edges_from( edges2remove )
    A.remove_nodes_from(nx.isolates(A))

    data = json_graph.node_link_data(A) # saving nodesA

    AB = nx.Graph()
    for i in NodesB_and_Docs:
        b = i
        docs = NodesB_and_Docs[i]
        for doc in docs:
            a = Docs_and_["nodesA"][doc]
            if A.has_node(a):
                AB.add_edge( a , b )
    AB_links = []
    for e in AB.edges_iter():
        info = { "s": e[0], "t": e[1], "w": 1 }
        AB_links.append(info)

    data["links"] = A_links + AB_links # saving AA-links and AB-links
            

    # = = = = [ / graph-A to JSON ] = = = = ]

    return data
