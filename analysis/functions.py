from gargantext_web.db import *

from collections import defaultdict
from django.db import connection, transaction

from math import log

def create_blacklist(user, corpus):
    pass

def create_synonymes(user, corpus):
    pass

def create_whitelist(user, corpus_id, size=100):
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
            COUNT(*) >= 1
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
def create_cooc(user=None, corpus_id=None, whitelist=None, size=150, year_start=None, year_end=None):
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

def get_cooc(request=None, corpus_id=None, cooc_id=None, type='node_link', n=150):
    import pandas as pd
    from copy import copy
    import numpy as np
    import networkx as nx
    from networkx.readwrite import json_graph
    from gargantext_web.api import JsonHttpResponse
    
    from analysis.louvain import best_partition

    matrix = defaultdict(lambda : defaultdict(float))
    ids    = dict()
    labels = dict()
    weight = dict()

    type_cooc_id = cache.NodeType['Cooccurrence'].id

    if session.query(Node).filter(Node.type_id==type_cooc_id, Node.parent_id==corpus_id).first() is None:
        print("Coocurrences do not exist yet, create it.")
        whitelist = create_whitelist(request.user, corpus_id=corpus_id, size=n)
        cooccurrence_node_id = create_cooc(user=request.user, corpus_id=corpus_id, whitelist=whitelist, size=n)
    else:
        cooccurrence_node_id = session.query(Node.id).filter(Node.type_id==type_cooc_id, Node.parent_id==corpus_id).first()

    for cooccurrence in session.query(NodeNgramNgram).filter(NodeNgramNgram.node_id==cooccurrence_node_id).all():
        # print(cooccurrence.ngramx.terms," <=> ",cooccurrence.ngramy.terms,"\t",cooccurrence.score)

        labels[cooccurrence.ngramx_id] = session.query(Ngram.terms).filter(Ngram.id == cooccurrence.ngramx_id).first()[0]
        labels[cooccurrence.ngramy_id] = session.query(Ngram.terms).filter(Ngram.id == cooccurrence.ngramy_id).first()[0]

        ids[labels[cooccurrence.ngramx_id]] = cooccurrence.ngramx_id
        ids[labels[cooccurrence.ngramy_id]] = cooccurrence.ngramy_id

        matrix[cooccurrence.ngramx_id][cooccurrence.ngramy_id] = cooccurrence.score
        matrix[cooccurrence.ngramy_id][cooccurrence.ngramx_id] = cooccurrence.score

        weight[cooccurrence.ngramx_id] = weight.get(cooccurrence.ngramx_id, 0) + cooccurrence.score
        weight[cooccurrence.ngramy_id] = weight.get(cooccurrence.ngramy_id, 0) + cooccurrence.score

    df = pd.DataFrame(matrix).fillna(0)
    x = copy(df.values)
    x = x / x.sum(axis=1)

    # import pprint
    # pprint.pprint(ids)

    # Removing unconnected nodes
    threshold = min(x.max(axis=1))
    matrix_filtered = np.where(x >= threshold, 1, 0)
    #matrix_filtered = np.where(x > threshold, x, 0)
    #matrix_filtered = matrix_filtered.resize((90,90))
    G = nx.from_numpy_matrix(matrix_filtered)
    G = nx.relabel_nodes(G, dict(enumerate([ labels[label] for label in list(df.columns)])))
    #G = nx.relabel_nodes(G, dict(enumerate(df.columns)))
    # Removing too connected nodes (find automatic way to do it)
    #    outdeg = G.degree()
    #    to_remove = [n for n in outdeg if outdeg[n] >= 10]
    #    G.remove_nodes_from(to_remove)

    partition = best_partition(G)
    
    if type == "node_link":
        
        for node in G.nodes():
            try:
                #node,type(labels[node])
                G.node[node]['id'] = ids[node]
                G.node[node]['label']   = node
                # G.node[node]['pk']      = ids[str(node)]
                G.node[node]['size']    = weight[ids[node]]
                G.node[node]['group']   = partition[node]
                # G.add_edge(node, "cluster " + str(partition[node]), weight=3)
            except Exception as error:
                print("error01: ",error)

        data = json_graph.node_link_data(G)
    
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


from analysis.tfidf import tfidf

def do_tfidf(corpus, reset=True):
    # print("=========== doing tfidf ===========")
    with transaction.atomic():
        if reset==True:
            NodeNodeNgram.objects.filter(nodex=corpus).delete()
        
        if isinstance(corpus, Node) and corpus.type.name == "Corpus":
            # print("\n- - - - - - - - - - ")
            # # for i in Node.objects.filter(parent=corpus, type=NodeType.objects.get(name="Document")):
            for document in Node.objects.filter(parent=corpus, type=NodeType.objects.get(name="Document")):
                # print("the doc:",document)
                for node_ngram in Node_Ngram.objects.filter(node=document):
                    # print("\tngram:",node_ngram.ngram)
                    try:
                        nnn = NodeNodeNgram.objects.get(nodex=corpus, nodey=document, ngram=node_ngram.ngram)
                        # print("\t\tTRY")
                    except:
                        score = tfidf(corpus, document, node_ngram.ngram)
                        nnn = NodeNodeNgram(nodex=corpus, nodey=node_ngram.node, ngram=node_ngram.ngram, score=score)
                        nnn.save()
                        # print("\t\t",node_ngram.ngram," : ",score)
            # print("- - - - - - - - - - \n")
        else:
            print("Only corpus implemented yet, you put instead:", type(corpus))





