# Gargantext lib
from gargantext.util.db           import session, aliased
from gargantext.util.lists        import WeightedMatrix, UnweightedList, Translations
from gargantext.util.http         import JsonHttpResponse
from gargantext.models            import Node, Ngram, NodeNgram, NodeNgramNgram, NodeHyperdata

from graph.cooccurrences          import countCooccurrences
from graph.distances              import clusterByDistances
from graph.bridgeness             import filterByBridgeness
from graph.mail_notification      import notify_owner
from graph.growth                 import compute_growth

from gargantext.util.scheduling   import scheduled
from gargantext.constants         import graph_constraints

from celery                       import shared_task
from datetime                     import datetime


@shared_task
def compute_graph( corpus_id=None      , cooc_id=None
                , field1='ngrams'     , field2='ngrams'
                , start=None          , end=None
                , mapList_id=None     , groupList_id=None
                , distance=None       , bridgeness=None
                , n_min=1, n_max=None , limit=1000
                , isMonopartite=True  , threshold = 3
                , save_on_db= True    , reset=True
                ) :
        '''
        All steps to compute a graph:

        1) count Cooccurrences  (function countCooccurrences)
                main parameters: threshold, isMonopartite

        2) filter and cluster By Distances (function clusterByDistances)
                main parameter: distance
                TODO option clustering='louvain'
                     or 'percolation' or 'random walk' or ...

        3) filter By Bridgeness (function filterByBridgeness)
                main parameter: bridgeness

        4) format the graph     (formatGraph)
                main parameter: format_
        '''

        print("GRAPH # ... Computing cooccurrences.")
        (cooc_id, cooc_matrix) = countCooccurrences( corpus_id=corpus_id, cooc_id=cooc_id
                                    , field1=field1, field2=field2
                                    , start=start           , end =end
                                    , mapList_id=mapList_id , groupList_id=groupList_id
                                    , isMonopartite=True    , threshold = threshold
                                    , distance=distance     , bridgeness=bridgeness
                                    , save_on_db = True     , reset = reset
                                    )
        print("GRAPH #%d ... Cooccurrences computed." % (cooc_id))


        print("GRAPH #%d ... Clustering with %s distance." % (cooc_id,distance))
        G, partition, ids, weight = clusterByDistances ( cooc_matrix
                                                       , field1="ngrams", field2="ngrams"
                                                       , distance=distance
                                                       )

        print("GRAPH #%d ... Filtering by bridgeness %d." % (cooc_id, bridgeness))
        data = filterByBridgeness(G,partition,ids,weight,bridgeness,"node_link",field1,field2)
        
        if start is not None and end is not None:
            growth= dict()
            for (ng_id, score) in compute_growth(corpus_id, groupList_id, mapList_id, start, end):
                growth[ng_id] = float(score) + 100 # for the normalization, should not be negativ

            for node in data['nodes']:
                node['attributes']['growth'] = growth[node['id']]
        
        print("GRAPH #%d ... Saving Graph in hyperdata as json." % cooc_id)
        node = session.query(Node).filter(Node.id == cooc_id).first()

        if node.hyperdata.get(distance, None) is None:
            print("GRAPH #%d ... Distance %s has not been computed already." % (cooc_id, distance))
            node.hyperdata[distance] = dict()

        node.hyperdata[distance][bridgeness] = data

        node.hyperdata[distance]["nodes"]    = len(G.nodes())
        node.hyperdata[distance]["edges"]    = len(G.edges())

        node.save_hyperdata()
        session.commit()

        print("GRAPH #%d ... Notify by email owner of the graph." % cooc_id)
        corpus = session.query(Node).filter(Node.id==corpus_id).first()
        #notify_owner(corpus, cooc_id, distance, bridgeness)

        print("GRAPH #%d ... Returning data as json." % cooc_id)
        return data

def get_graph( request=None         , corpus=None
            , field1='ngrams'       , field2='ngrams'
            , mapList_id = None     , groupList_id = None
            , cooc_id=None          , type='node_link'
            , start=None            , end=None
            , distance='conditional', bridgeness=5
            , threshold=1           , isMonopartite=True
            , saveOnly=True
            ) :
    '''
    Get_graph : main steps:
    0) Check the parameters

    get_graph :: GraphParameters -> Either (Dic Nodes Links) (Dic State Length)
        where type Length = Int

    get_graph first checks the parameters and return either graph data or a dict with
    state "type" with an integer to indicate the size of the parameter
    (maybe we could add a String in that step to factor and give here the error message)

    1) compute_graph (see function above)
    2) return graph

    '''
    overwrite_node_contents = False

    # Case of graph has been computed already
    if cooc_id is not None:
        print("GRAPH#%d ... Loading data already computed." % int(cooc_id))
        node = session.query(Node).filter(Node.id == cooc_id).first()

        # Structure of the Node.hyperdata[distance][bridbeness]
        # All parameters (but distance and bridgeness)
        # are in Node.hyperdata["parameters"]

        # Check distance of the graph
        if node.hyperdata.get(distance, None) is not None:
            graph = node.hyperdata[distance]

            # Check bridgeness of the graph
            if graph.get(str(bridgeness), None) is not None:
                return graph[str(bridgeness)]

    # new graph: we give it an empty node with new id and status
    elif saveOnly:
        # NB: we do creation already here (instead of same in countCooccurrences)
        #     to guarantee a unique ref id to the saveOnly graph (async generation)
        new_node = corpus.add_child(
                            typename  = "COOCCURRENCES",
                            name = "GRAPH (in corpus %s)" % corpus.id
                            )

        session.add(new_node)
        session.commit()
        cooc_id = new_node.id
        cooc_name = new_node.name
        cooc_date = new_node.date
        # and the empty content will need redoing by countCooccurrences
        overwrite_node_contents = True
        print("GRAPH #%d ... Created new empty data node for saveOnly" % int(cooc_id))



    # Case of graph has not been computed already
    # First, check the parameters

    # Case of mapList not big enough
    # ==============================

    # if we do not have any mapList_id already
    if mapList_id is None:
        mapList_id = session.query(Node.id).filter(Node.typename == "MAPLIST").first()[0]

    mapList_size = session.query(NodeNgram).filter(NodeNgram.node_id == mapList_id).count()

    if mapList_size < graph_constraints['mapList']:
        # Do not compute the graph if mapList is not big enough
        return {'state': "mapListError", "length" : mapList_size}


    # Instantiate query for case of corpus not big enough
    # ===================================================
    corpus_size_query = (session.query(Node)
                                .filter(Node.typename=="DOCUMENT")
                                .filter(Node.parent_id == corpus.id)
                        )

    # Filter corpus by date if any start date
    # ---------------------------------------
    if start is not None:
        #date_start = datetime.datetime.strptime ("2001-2-3 10:11:12", "%Y-%m-%d %H:%M:%S")
        date_start = datetime.strptime (str(start), "%Y-%m-%d")
        date_start_utc = date_start.strftime("%Y-%m-%d %H:%M:%S")

        Start=aliased(NodeHyperdata)
        corpus_size_query = (corpus_size_query.join( Start
                                     , Start.node_id == Node.id
                                     )
                                .filter( Start.key == 'publication_date')
                                .filter( Start.value_utc >= date_start_utc)
                            )


    # Filter corpus by date if any end date
    # -------------------------------------
    if end is not None:
        date_end = datetime.strptime (str(end), "%Y-%m-%d")
        date_end_utc = date_end.strftime("%Y-%m-%d %H:%M:%S")

        End=aliased(NodeHyperdata)

        corpus_size_query = (corpus_size_query.join( End
                                     , End.node_id == Node.id
                                     )
                                .filter( End.key == 'publication_date')
                                .filter( End.value_utc <= date_end_utc )
                            )

    # Finally test if the size of the corpora is big enough
    # --------------------------------
    corpus_size = corpus_size_query.count()

    if saveOnly is not None and saveOnly == "True":
        scheduled(compute_graph)( corpus_id=corpus.id, cooc_id=cooc_id
                                   #, field1="ngrams", field2="ngrams"
                                    , start=start           , end =end
                                    , mapList_id=mapList_id , groupList_id=groupList_id
                                    , isMonopartite=True    , threshold = threshold
                                    , distance=distance     , bridgeness=bridgeness
                                    , save_on_db = True     , reset=overwrite_node_contents
                                   #, limit=size
                                    )

        return { "state"      : "saveOnly"
               , "target_id"  : cooc_id
               , "target_name": cooc_name
               , "target_date": cooc_date
               }

    elif corpus_size > graph_constraints['corpusMax']:
        # Then compute cooc asynchronously with celery
        scheduled(compute_graph)( corpus_id=corpus.id, cooc_id=cooc_id
                                   #, field1="ngrams", field2="ngrams"
                                    , start=start           , end =end
                                    , mapList_id=mapList_id , groupList_id=groupList_id
                                    , isMonopartite=True    , threshold = threshold
                                    , distance=distance     , bridgeness=bridgeness
                                    , save_on_db = True     , reset=overwrite_node_contents
                                   #, limit=size
                                    )
        # Dict to inform user that corpus maximum is reached
        # then graph is computed asynchronously
        return {"state" : "corpusMax", "length" : corpus_size}

    elif corpus_size <= graph_constraints['corpusMin']:
        # Do not compute the graph if corpus is not big enough
        return {"state" : "corpusMin", "length" : corpus_size}

    else:
        # If graph_constraints are ok then compute the graph in live
        data = compute_graph( corpus_id=corpus.id, cooc_id=cooc_id
                                  #, field1="ngrams", field2="ngrams"
                                   , start=start           , end =end
                                   , mapList_id=mapList_id , groupList_id=groupList_id
                                   , isMonopartite=True    , threshold = threshold
                                   , distance=distance     , bridgeness=bridgeness
                                   , save_on_db = True     , reset=overwrite_node_contents
                                  #, limit=size
                                   )

    # case when 0 coocs are observed (usually b/c not enough ngrams in maplist)

    if len(data) == 0:
        print("GRAPH #   ... GET_GRAPH: 0 coocs in matrix")
        data = {'nodes':[], 'links':[]}  # empty data
    
    return data
