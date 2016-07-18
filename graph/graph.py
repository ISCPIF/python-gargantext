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
            #, size=1000
        ):
    '''
    Get_graph : main steps:
    1) count Cooccurrences  (function countCooccurrences)
            main parameters: threshold

    2) filter and cluster By Distances (function clusterByDistances)
            main parameter: distance

    3) filter By Bridgeness (filter By Bridgeness)
            main parameter: bridgness

    4) format the graph     (formatGraph)
            main parameter: format_

    '''


    before_cooc = datetime.now()
    

    # case of Cooccurrences have not been computed already
    if cooc_id == None:

        # case of mapList not big enough
        # ==============================
        # if we do not have any mapList_id already
        if mapList_id is None:
            mapList_id = session.query(Node.id).filter(Node.typename == "MAPLIST").first()[0]

        mapList_size = session.query(NodeNgram).filter(NodeNgram.node_id == mapList_id)
        
        if mapList_size.count() < graph_constraints['mapList']:
            # Do not compute the graph if mapList is not big enough
            return {'nodes':[mapList_size.count()], 'links':[0,0,0]}


        # case of corpus not big enough
        # ==============================
        corpus_size_query = (session.query(Node)
                                    .filter(Node.typename=="DOCUMENT")
                                    .filter(Node.parent_id == corpus.id)
                            )

        # filter by date if any start date
        # --------------------------------
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


        # filter by date if any end date
        # --------------------------------
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
        if corpus_size_query.count() > graph_constraints['corpusMax']:
            # Then compute cooc asynchronously with celery
            scheduled(countCooccurrences)( corpus_id=corpus.id
                                       #, field1="ngrams", field2="ngrams"
                                        , start=start           , end =end
                                        , mapList_id=mapList_id , groupList_id=groupList_id
                                        , isMonopartite=True    , threshold = threshold
                                        , save_on_db = True
                                       #, limit=size
                                        )
            # Dic hack to inform user that graph is computed asynchronously
            # (Impossible graph: no nodes with one link)
            return {'nodes':[], 'links':[0]}  
        
        elif corpus_size_query.count() <= graph_constraints['corpusMin']:
            # Do not compute the graph if corpus is not big enough
            return {'nodes':[corpus_size_query.count()], 'links':[0,0]}  
  
        else:
            # If graph_constraints are ok then compute the graph in live
            cooc_matrix = countCooccurrences( corpus_id=corpus.id
                                       #, field1="ngrams", field2="ngrams"
                                        , start=start           , end =end
                                        , mapList_id=mapList_id , groupList_id=groupList_id
                                        , isMonopartite=True    , threshold = threshold
                                        , save_on_db = False
                                       #, limit=size
                                        )
    else:
        print("Getting data for matrix %d", int(cooc_id))
        matrix      = WeightedMatrix(int(cooc_id))
        #print(matrix)
        cooc_matrix = filterMatrix(matrix, mapList_id, groupList_id)


    # fyi
    after_cooc = datetime.now()
    print("... Cooccurrences took %f s." % (after_cooc - before_cooc).total_seconds())


    # case when 0 coocs are observed (usually b/c not enough ngrams in maplist)
    if len(cooc_matrix.items) == 0:
        print("GET_GRAPH: 0 coocs in matrix")
        data = {'nodes':[], 'links':[]}  # empty data

    # normal case
    else:
        G, partition, ids, weight = clusterByDistances ( cooc_matrix
                                                       , field1="ngrams", field2="ngrams"
                                                       , distance=distance
                                                       )

        after_cluster = datetime.now()
        print("... Clustering took %f s." % (after_cluster - after_cooc).total_seconds())

        data = filterByBridgeness(G,partition,ids,weight,bridgeness,type,field1,field2)

        after_filter = datetime.now()
        print("... Filtering took %f s." % (after_filter - after_cluster).total_seconds())

    return data
