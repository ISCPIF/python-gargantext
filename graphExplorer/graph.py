# Gargantext lib
from gargantext.util.db           import session
from gargantext.util.http         import JsonHttpResponse
from gargantext.models            import Node, Ngram, NodeNgram, NodeNgramNgram

#from gargantext.util.toolchain.ngram_coocs import compute_coocs
from graphExplorer.cooccurrences  import countCooccurrences
from graphExplorer.distances      import clusterByDistances
from graphExplorer.bridgeness     import filterByBridgeness

# Prelude lib
from copy                         import copy, deepcopy
from collections                  import defaultdict
from sqlalchemy.orm               import aliased

# Math/Graph lib
import math
import pandas                     as pd
import numpy                      as np

import networkx                   as nx


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

    if cooc_id == None:
        cooc_id = countCooccurrences( corpus=corpus
                                   #, field1="ngrams", field2="ngrams"
                                    , start=start           , end =end
                                    , mapList_id=mapList_id , groupList_id=groupList_id
                                    , isMonopartite=True    , threshold = threshold
                                   #, limit=size
                                    )
    
    G, partition, ids, weight = clusterByDistances ( cooc_id
                                                   , field1="ngrams", field2="ngrams"
                                                   , distance=distance
                                                   )
    
    data = filterByBridgeness(G,partition,ids,weight,bridgeness,type,field1,field2)
    
    return data

