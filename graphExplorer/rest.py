#from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from gargantext.util.db      import session
from gargantext.models.nodes import Node
from graphExplorer.functions import get_cooc
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
        # implicit global session
        
        field1      = str(request.GET.get ('field1'    , 'ngrams'     ))
        field2      = str(request.GET.get ('field2'    , 'ngrams'     ))
        
        start       = request.GET.get     ('start'     , None         )
        end         = request.GET.get     ('end'       , None         )
        
        threshold   = int(request.GET.get ('threshold' , 1            ))
        bridgeness  = int(request.GET.get ('bridgeness', -1           ))
        format_     = str(request.GET.get ('format'    , 'json'       ))
        type_       = str(request.GET.get ('type'      , 'node_link'  ))
        distance    = str(request.GET.get ('distance'  , 'conditional'))
        

        corpus = session.query(Node).filter(Node.id==corpus_id).first()
        
        accepted_field1 = ['ngrams', 'journal', 'source', 'authors']
        accepted_field2 = ['ngrams',]
        options         = ['start', 'end', 'threshold', 'distance']
        
        if field1 in accepted_field1 :
            if field2 in accepted_field2 :
                if start is not None and end is not None :
                    data = get_cooc( corpus=corpus
                                  #, field1=field1     , field2=field2
                                   , start=start        , end=end
                                   , threshold =threshold   , distance=distance
                                   )
                else:
                    data = get_cooc( corpus = corpus
                                  #, field1=field1, field2=field2
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
