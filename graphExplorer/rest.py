#from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from gargantext.util.db      import session
from gargantext.models.nodes import Node
from graphExplorer.graph     import get_graph
from gargantext.util.http    import APIView, APIException\
                                  , JsonHttpResponse, requires_auth

# TODO check authentication

class Graph(APIView):
    '''
    REST part for graphs.
    '''
    def get(self, request, project_id, corpus_id):
        '''
        Graph.get :: Get graph data as REST api.
        Get all the parameters first
        graph?field1=ngrams&field2=ngrams&
        graph?field1=ngrams&field2=ngrams&start=''&end=''
        '''
        
        # Get the node we are working with
        corpus = session.query(Node).filter(Node.id==corpus_id).first()
        
        # Get all the parameters in the URL
        field1       = str(request.GET.get ('field1'    , 'ngrams'     ))
        field2       = str(request.GET.get ('field2'    , 'ngrams'     ))
        
        start        = request.GET.get     ('start'     , None         )
        end          = request.GET.get     ('end'       , None         )
        
        mapList_id   = int(request.GET.get ('mapList'   , 0            ))
        groupList_id = int(request.GET.get ('groupList' , 0            ))
        
        threshold    = int(request.GET.get ('threshold' , 1            ))
        bridgeness   = int(request.GET.get ('bridgeness', -1           ))
        format_      = str(request.GET.get ('format'    , 'json'       ))
        type_        = str(request.GET.get ('type'      , 'node_link'  ))
        distance     = str(request.GET.get ('distance'  , 'conditional'))
        
        # Get default value if no map list
        if mapList_id == 0 :
            mapList_id = ( session.query ( Node.id )
                                    .filter( Node.typename  == "MAPLIST"
                                           , Node.parent_id == corpus.id
                                           )
                                    .first()
                          )
            
            mapList_id = mapList_id[0]
            
            if mapList_id == None :
                raise ValueError("MAPLIST node needed for cooccurrences")


        # Get default value if no group list
        if groupList_id  == 0 :
            groupList_id  = ( session.query ( Node.id )
                                     .filter( Node.typename  == "GROUPLIST"
                                            , Node.parent_id == corpus.id
                                            )
                                     .first()
                            )
            
            groupList_id  = groupList_id[0]
            
            if groupList_id == None :
                raise ValueError("GROUPLIST node needed for cooccurrences")


        # Chec the options
        accepted_field1 = ['ngrams', 'journal', 'source', 'authors']
        accepted_field2 = ['ngrams',                               ]
        options         = ['start', 'end', 'threshold', 'distance' ]
        
        if field1 in accepted_field1 :
            if field2 in accepted_field2 :
                if start is not None and end is not None :
                    data = get_graph( corpus=corpus
                                  #, field1=field1           , field2=field2
                                   , mapList_id = mapList_id , groupList_id = groupList_id
                                   , start=start             , end=end
                                   , threshold =threshold    , distance=distance
                                   )
                else:
                    data = get_graph( corpus = corpus
                                  #, field1=field1, field2=field2
                                   , mapList_id = mapList_id , groupList_id = groupList_id
                                   , threshold  = threshold
                                   , distance   = distance
                                   , bridgeness = bridgeness
                                   )
                if format_ == 'json':
                    return JsonHttpResponse(data)
        else:
            return JsonHttpResponse({
                'Warning USAGE' : 'One field for each range:'
                , 'field1' : accepted_field1
                , 'field2' : accepted_field2
                , 'options': options
                })
