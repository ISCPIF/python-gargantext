# Gargantext lib
from gargantext.util.db           import session, aliased
from gargantext.util.lists        import WeightedMatrix, UnweightedList, Translations
from gargantext.util.http         import JsonHttpResponse
from gargantext.models            import Node, Ngram, NodeNgram, NodeNgramNgram, NodeHyperdata

#from gargantext.util.toolchain.ngram_coocs import compute_coocs
from graph.cooccurrences  import countCooccurrences, filterMatrix
from graph.distances      import clusterByDistances
from graph.bridgeness     import filterByBridgeness

from gargantext.util.scheduling import scheduled
from gargantext.constants import graph_constraints

from datetime import datetime

def get_graph( request=None         , corpus=None
            , field1='ngrams'       , field2='ngrams'
            , mapList_id = None     , groupList_id = None
            , cooc_id=None          , type='node_link'
            , start=None            , end=None
            , threshold=1
            , distance='conditional'
            , isMonopartite=True                # By default, we compute terms/terms graph
            , bridgeness=5
            , saveOnly=None
            #, size=1000
        ):
    '''
    Get_graph : main steps:
    0) Check the parameters
    
    get_graph :: GraphParameters -> Either (Dic Nodes Links) (Dic State Length)
        where type Length = Int

    get_graph first checks the parameters and return either graph data or a dict with 
    state "type" with an integer to indicate the size of the parameter 
    (maybe we could add a String in that step to factor and give here the error message)

    1) count Cooccurrences  (function countCooccurrences)
            main parameters: threshold

    2) filter and cluster By Distances (function clusterByDistances)
            main parameter: distance

    3) filter By Bridgeness (function filterByBridgeness)
            main parameter: bridgeness

    4) format the graph     (formatGraph)
            main parameter: format_

    '''


    # Case of graph has been computed already
    if cooc_id is not None:
        print("Getting data for matrix %d", int(cooc_id))
        node = session.query(Node).filter(Node.id == cooc_id).first()
        
        # Check if 
        if node.hyperdata.get(distance, None) is not None:
            data = node.hyperdata[distance]["data"]
            return data


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
        scheduled(countCooccurrences)( corpus_id=corpus.id, coocNode_id=cooc_id
                                   #, field1="ngrams", field2="ngrams"
                                    , start=start           , end =end
                                    , mapList_id=mapList_id , groupList_id=groupList_id
                                    , isMonopartite=True    , threshold = threshold
                                    , distance=distance     , bridgeness=bridgeness
                                    , save_on_db = True
                                   #, limit=size
                                    )
        return {"state" : "saveOnly"}

    if corpus_size > graph_constraints['corpusMax']:
        # Then compute cooc asynchronously with celery
        scheduled(countCooccurrences)( corpus_id=corpus.id, coocNode_id=cooc_id
                                   #, field1="ngrams", field2="ngrams"
                                    , start=start           , end =end
                                    , mapList_id=mapList_id , groupList_id=groupList_id
                                    , isMonopartite=True    , threshold = threshold
                                    , distance=distance     , bridgeness=bridgeness
                                    , save_on_db = True
                                   #, limit=size
                                    )
        # Dict to inform user that corpus maximum is reached then
        # graph is computed asynchronously
        return {"state" : "corpusMax", "length" : corpus_size}

    elif corpus_size <= graph_constraints['corpusMin']:
        # Do not compute the graph if corpus is not big enough
        return {"state" : "corpusMin", "length" : corpus_size}

    else:
        # If graph_constraints are ok then compute the graph in live
        data = countCooccurrences( corpus_id=corpus.id, coocNode_id=cooc_id
                                  #, field1="ngrams", field2="ngrams"
                                   , start=start           , end =end
                                   , mapList_id=mapList_id , groupList_id=groupList_id
                                   , isMonopartite=True    , threshold = threshold
                                   , distance=distance     , bridgeness=bridgeness
                                   , save_on_db = True
                                  #, limit=size
                                   )

    # case when 0 coocs are observed (usually b/c not enough ngrams in maplist)

    if len(data) == 0:
        print("GET_GRAPH: 0 coocs in matrix")
        data = {'nodes':[], 'links':[]}  # empty data

    return data
