from node.models import Language, ResourceType, Resource, \
        Node, NodeType, Node_Resource, Project, Corpus, \
        Node_Ngram, NodeNgramNgram

from collections import defaultdict
from django.db import connection, transaction

def create_blacklist(user, corpus):
    pass

def create_synonymes(user, corpus):
    pass

def create_whitelist(user, corpus):
    cursor = connection.cursor()
    
    try:
        whitelist_type = NodeType.objects.get(name='WhiteList')
        blacklist_type = NodeType.objects.get(name='BlackList')
        type_document  = NodeType.objects.get(name='Document')
    except:
        whitelist_type = NodeType(name='WhiteList')
        whitelist_type.save()
    
        blacklist_type = NodeType(name='BlackList')
        blacklist_type.save()

    white_list = Node.objects.create(name='WhiteList Corpus ' + str(corpus.id), user=user, parent=corpus, type=whitelist_type)
    black_list = Node.objects.create(name='BlackList Corpus ' + str(corpus.id), user=user, parent=corpus, type=blacklist_type)

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
            ngX.n >= 1

        GROUP BY
            ngX.id
        Having
            COUNT(*) >= 1
        ORDER BY
            occurrences DESC
        LIMIT
            100
        ;
    """  % (white_list.id, corpus.id, type_document.id)

    cursor.execute(query_whitelist)

    return white_list

#def create_cooc(user, corpus, whitelist, blacklist, synonymes):
def create_cooc(user=None, corpus=None, whitelist=None, size=200):
    cursor = connection.cursor()

    try:
        cooc_type  = NodeType.objects.get(name='Cooccurrence')
    except:
        cooc_type = NodeType(name='Cooccurrence')
        cooc_type.save()
    # pour les tests on supprime les cooc
    Node.objects.filter(type=cooc_type, parent=corpus).delete()

    cooc = Node.objects.create(user=user,\
                           parent=corpus,\
                           type=cooc_type,\
                           name="Cooccurrences corpus " + str(corpus.pk))

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
    """ % (cooc.pk, corpus.id, whitelist.id, whitelist.id, size)

    cursor.execute(query_cooc)
    return cooc

def get_cooc(request=None, corpus_id=None, cooc_id=None, type="node_link"):
    import pandas as pd
    from copy import copy
    import numpy as np
    import networkx as nx
    from networkx.readwrite import json_graph
    from gargantext_web.api import JsonHttpResponse
    
    from analysis.louvain import best_partition

    matrix = defaultdict(lambda : defaultdict(float))
    labels = dict()
    weight = dict()

    corpus = Node.objects.get(id=corpus_id)
    type_cooc = NodeType.objects.get(name="Cooccurrence")

    if Node.objects.filter(type=type_cooc, parent=corpus).first() is None:
        print("Coocurrences do not exist yet, create it.")
        whitelist = create_whitelist(request.user, corpus)
        cooccurrence_node = create_cooc(user=request.user, corpus=corpus, whitelist=whitelist)
        print(cooccurrence_matrix.id, "Cooc created")
    else:
        cooccurrence_node = Node.objects.filter(type=type_cooc, parent=corpus).first()

    for cooccurrence in NodeNgramNgram.objects.filter(node=cooccurrence_node):
        labels[cooccurrence.ngramx.id] = cooccurrence.ngramx.terms
        labels[cooccurrence.ngramy.id] = cooccurrence.ngramy.terms
        
        matrix[cooccurrence.ngramx.id][cooccurrence.ngramy.id] = cooccurrence.score
        matrix[cooccurrence.ngramy.id][cooccurrence.ngramx.id] = cooccurrence.score

        weight[cooccurrence.ngramy.terms] = weight.get(cooccurrence.ngramy.terms, 0) + cooccurrence.score
        weight[cooccurrence.ngramx.terms] = weight.get(cooccurrence.ngramx.terms, 0) + cooccurrence.score


    df = pd.DataFrame(matrix).T.fillna(0)
    x = copy(df.values)
    x = x / x.sum(axis=1)

    # Removing unconnected nodes
    threshold = min(x.max(axis=1))
    matrix_filtered = np.where(x >= threshold, 1, 0)
    #matrix_filtered = np.where(x > threshold, x, 0)
    
    G = nx.from_numpy_matrix(matrix_filtered)
    G = nx.relabel_nodes(G, dict(enumerate([ labels[label] for label in list(df.columns)])))
    #G = nx.relabel_nodes(G, dict(enumerate(df.columns)))
    
    # Removing too connected nodes (find automatic way to do it)
#    outdeg = G.degree()
#    to_remove = [n for n in outdeg if outdeg[n] >= 10]
#    G.remove_nodes_from(to_remove)

    partition = best_partition(G)
    
    for node in G.nodes():
        try:
            #node,type(labels[node])
            G.node[node]['label']   = node
            G.node[node]['name']    = node
            G.node[node]['size']    = weight[node]
            G.node[node]['group']   = partition[node]
#            G.node[node]['color'] = '19,180,300'
            G.add_edge(node, partition[node], weight=2)
        except Exception as error:
            print(error)
    
    if type == "node_link":
        data = json_graph.node_link_data(G)
    elif type == "adjacency":
        data = json_graph.adjacency_data(G)
#    data = json_graph.node_link_data(G, attrs={\
#            'source':'source',\
#            'target':'target',\
#            'weight':'weight',\
#            #'label':'label',\
#            #'color':'color',\
#            'id':'id',})
    #print(data)
    return data







