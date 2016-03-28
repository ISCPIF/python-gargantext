# Gargantext lib
from gargantext.util.db           import session
from gargantext.util.http         import JsonHttpResponse
from gargantext.models            import Node, Ngram, NodeNgram, NodeNgramNgram

#from gargantext.util.toolchain.ngram_coocs import compute_coocs
from graphExplorer.distance       import do_distance
from graphExplorer.cooccurrences  import do_cooc

# Prelude lib
from copy                         import copy, deepcopy
from collections                  import defaultdict
from sqlalchemy.orm               import aliased

# Math/Graph lib
import math
import pandas   as pd
import numpy    as np

import networkx as nx
from networkx.readwrite           import json_graph


def get_cooc( request=None, corpus=None
            , field1='ngrams', field2='ngrams'
            , cooc_id=None   , type='node_link'
            , start=None     , end=None
            , threshold=1
            , distance='conditional'
            , size=1000
            , bridgeness=5
            , mainList_id = None , groupList_id = None
        ):
    '''
    get_ccoc : to compute the graph.
    '''

    data = {}


    if mainList_id == None :
        mainList_id  = ( session.query ( Node.id )
                                .filter( Node.typename  == "MAINLIST"
                                       , Node.parent_id == corpus.id
                                       )
                                .first()
                       )
        if mainList_id == None :
            raise ValueError("MAINLIST node needed for cooccurrences")


    if groupList_id   == None :
        groupList_id  = ( session.query ( Node.id )
                                 .filter( Node.typename  == "GROUPLIST"
                                        , Node.parent_id == corpus.id
                                        )
                                 .first()
                        )
        
        if groupList_id == None :
            raise ValueError("GROUPLIST node needed for cooccurrences")


    # compute_cooc needs group, fields etc.
    # group_id = 3
    
    SamuelFlag = False
    # if field1 == field2 == 'ngrams' :
    #     isMonopartite = True
    #     SamuelFlag = True
    # else:
    #     isMonopartite = False
    isMonopartite = True # Always. So, calcule the graph B and from these B-nodes, build the graph-A
    # data deleted each time
    #cooc_id = get_or_create_node(nodetype='Cooccurrence', corpus=corpus).id
    
    if corpus is None:
        corpus = session.query(Node).filter(Node.id==corpus_id).first()

    cooc_id = do_cooc( corpus=corpus
                    #, field1="ngrams", field2="ngrams"
                     , mainList_id=int(mainList_id[0]), groupList_id=int(groupList_id[0])
                    #, isMonopartite=True
                     , start=start    , end =end
                     , threshold      = threshold #, limit=size
                     )
    
    G, partition, ids, weight = do_distance ( cooc_id
                                            , field1="ngrams", field2="ngrams"
                                            , isMonopartite=True
                                            , distance=distance
                                            )
    if type == "node_link":
        nodesB_dict = {}
        for node_id in G.nodes():
            #node,type(labels[node])
            G.node[node_id]['pk'] = ids[node_id][1]
            nodesB_dict [ ids[node_id][1] ] = True
            # TODO the query below is not optimized (do it do_distance).
            the_label = session.query(Ngram.terms).filter(Ngram.id==node_id).first()
            the_label = ", ".join(the_label)
            G.node[node_id]['label']   = the_label
            
            G.node[node_id]['size']    = weight[node_id]
            G.node[node_id]['type']    = ids[node_id][0].replace("ngrams","terms")
            G.node[node_id]['attributes'] = { "clust_default": partition[node_id]} # new format
            # G.add_edge(node, "cluster " + str(partition[node]), weight=3)

        

        links = []
        i=1
        

        if bridgeness > 0:
            com_link = defaultdict(lambda: defaultdict(list))
            com_ids = defaultdict(list)
            
            for k, v in partition.items():
                com_ids[v].append(k)
        

        for e in G.edges_iter():
            s = e[0]
            t = e[1]
            weight = G[ids[s][1]][ids[t][1]]["weight"]
            
            if bridgeness < 0:
                info = { "s": ids[s][1]
                       , "t": ids[t][1]
                       , "w": weight
                       }
                links.append(info)
            
            else:
                if partition[s] == partition[t]:

                    info = { "s": ids[s][1]
                           , "t": ids[t][1]
                           , "w": weight
                           }
                    links.append(info)
                
                if bridgeness > 0:
                    if partition[s] < partition[t]:
                        com_link[partition[s]][partition[t]].append((s,t,weight))
        
        if bridgeness > 0:
            for c1 in com_link.keys():
                for c2 in com_link[c1].keys():
                    index = round(bridgeness*len(com_link[c1][c2]) / (len(com_ids[c1]) + len(com_ids[c2])))
                    #print((c1,len(com_ids[c1])), (c2,len(com_ids[c2])), index)
                    if index > 0:
                        for link in sorted(com_link[c1][c2], key=lambda x: x[2], reverse=True)[:index]:
                            #print(c1, c2, link[2])
                            info = {"s": link[0], "t": link[1], "w": link[2]}
                            links.append(info)


        B = json_graph.node_link_data(G)
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
