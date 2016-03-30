# Gargantext lib
from gargantext.util.db           import session
from gargantext.util.http         import JsonHttpResponse
from gargantext.models            import Node, Ngram, NodeNgram, NodeNgramNgram

#from gargantext.util.toolchain.ngram_coocs import compute_coocs
from graphExplorer.distances      import do_distance
from graphExplorer.cooccurrences  import do_cooc

# Prelude lib
from copy                         import copy, deepcopy
from collections                  import defaultdict
from sqlalchemy.orm               import aliased

# Math/Graph lib
import math
import pandas                     as pd
import numpy                      as np

import networkx                   as nx
from networkx.readwrite           import json_graph


def get_cooc( request=None, corpus=None
            , field1='ngrams', field2='ngrams'
            , cooc_id=None   , type='node_link'
            , start=None     , end=None
            , threshold=1
            , distance='conditional'
            , isMonopartite=True                # By default, we compute terms/terms graph
            , size=1000
            , bridgeness=5
            , mapList_id = None , groupList_id = None
        ):
    '''
    get_ccoc : to compute the graph.
    '''


    if mapList_id == None :
        mapList_id  = ( session.query ( Node.id )
                                .filter( Node.typename  == "MAPLIST"
                                       , Node.parent_id == corpus.id
                                       )
                                .first()
                       )
        if mapList_id == None :
            raise ValueError("MAPLIST node needed for cooccurrences")


    if groupList_id   == None :
        groupList_id  = ( session.query ( Node.id )
                                 .filter( Node.typename  == "GROUPLIST"
                                        , Node.parent_id == corpus.id
                                        )
                                 .first()
                        )

        if groupList_id == None :
            raise ValueError("GROUPLIST node needed for cooccurrences")


    if corpus is None:
        corpus = session.query(Node).filter(Node.id==corpus_id).first()

    cooc_id = do_cooc( corpus=corpus
                    #, field1="ngrams", field2="ngrams"
                     , mapList_id=int(mapList_id[0]), groupList_id=int(groupList_id[0])
                    #, isMonopartite=True
                     , start=start    , end =end
                     , threshold      = threshold #, limit=size
                     )
    
    G, partition, ids, weight = do_distance ( cooc_id
                                            , field1="ngrams", field2="ngrams"
                                            , isMonopartite=True
                                            , distance=distance
                                            )
    # Data are stored in a dict(), (== hashmap by default for Python)
    data = dict()
    
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


