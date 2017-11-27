# Article coming soon

from gargantext.util.db       import session
from gargantext.models.ngrams import Ngram
from collections              import defaultdict

from networkx.readwrite           import json_graph

def filterByBridgeness(G,partition,ids,weight,bridgeness,type,field1,field2):
    '''
    Bridgeness = measure to control links (bridges) between communities.
    '''
    # Data are stored in a dict(), (== hashmap by default with Python)
    data = dict()
    if type == "node_link":
        nodesB_dict = {}
        for node_id in G.nodes():
            #node,type(labels[node])
            nodesB_dict [ ids[node_id][1] ] = True
            
            # TODO the query below is not optimized (do it do_distance).
            the_label = session.query(Ngram.terms).filter(Ngram.id==node_id).first()
            the_label = ", ".join(the_label)
            
            
            G.node[node_id]['label']        = the_label

            G.node[node_id]['size']         = weight[node_id]
            
            G.node[node_id]['type']         = ids[node_id][0].replace("ngrams","terms")
            
            G.node[node_id]['attributes']   = { "clust_default": partition[node_id]} # new format
            # G.add_edge(node, "cluster " + str(partition[node]), weight=3)

        links = []
        i=1

        if bridgeness > 0:
            com_link = defaultdict(lambda: defaultdict(list))
            com_ids = defaultdict(list)

            for k, v in partition.items():
                com_ids[v].append(k)

        edge_id = 1
        
        for e in G.edges_iter():
            s = e[0]
            t = e[1]
            weight = G[ids[s][1]][ids[t][1]]["weight"]

            if bridgeness < 0:
                info = { "source": ids[s][1]
                       , "target": ids[t][1]
                       , "weight": weight
                       }
                links.append(info)

            else:
                if partition[s] == partition[t]:

                    info = { "source": ids[s][1]
                           , "target": ids[t][1]
                           , "weight": weight
                           }
                    links.append(info)

                if bridgeness > 0:
                    if partition[s] < partition[t]:
                        com_link[partition[s]][partition[t]].append((s,t,weight))

        if bridgeness > 0:
            for c1 in com_link.keys():
                for c2 in com_link[c1].keys():
                    index = round(
                                     bridgeness * len( com_link[c1][c2] )
                                   / #----------------------------------#
                                   ( len(com_ids[c1]) + len(com_ids[c2] ))
                                 )
                    #print((c1,len(com_ids[c1])), (c2,len(com_ids[c2])), index)
                    if index > 0:
                        for link in sorted( com_link[c1][c2]
                                          , key=lambda x: x[2]
                                          , reverse=True)[:index]:
                            #print(c1, c2, link[2])
                            
                            info = {"source": link[0], "target": link[1], "weight": link[2]}
                            
                            links.append(info)


        B = json_graph.node_link_data(G)

        links_id = []
        edge_id = 0
        for link in links:
            edge_id += 1
            link["id"] = edge_id
            links_id.append(link)

        B["edges"] = []
        B["edges"] = links_id
        if field1 == field2 == 'ngrams' :
            data["nodes"] = B["nodes"]
            data["edges"] = B["edges"]
        else:
            A = get_graphA( "journal" , nodesB_dict , B["edges"] , corpus )
            print("#nodesA:",len(A["nodes"]))
            print("#linksAA + #linksAB:",len(A["links"]))
            print("#nodesB:",len(B["nodes"]))
            print("#linksBB:",len(B["links"]))
            data["nodes"] = A["nodes"] + B["nodes"]
            data["edges"] = A["edges"] + B["edges"]
            print("  total nodes :",len(data["nodes"]))
            print("  total links :",len(data["edges"]))
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
