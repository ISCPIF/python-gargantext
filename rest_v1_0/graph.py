from rest_v1_0.api import APIView, APIException, JsonHttpResponse, CsvHttpResponse
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from gargantext_web.db import session, Node
from analysis.functions import get_cooc

class Graph(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    def get(self, request, corpus_id):
        '''
        Graph.get :: Get graph data as REST api.
        Get all the parameters first
        graph?field1=ngrams&field2=ngrams&
        graph?field1=ngrams&field2=ngrams&start=''&end=''
        '''
        field1 = request.GET.get('field1', 'ngrams')
        field2 = request.GET.get('field2', 'ngrams')
        
        start  = request.GET.get('start', None)
        end    = request.GET.get('end'  , None)
        
        format_   =  request.GET.get('format', 'json')
        type_    = request.GET.get('type', 'node_link')
        apax    = request.GET.get('apax', 1)
        

        corpus = session.query(Node).filter(Node.id==corpus_id).first()
        
        accepted_field1 = ['ngrams', 'journal', 'source', 'authors']
        accepted_field2 = ['ngrams',]
        options = ['start', 'end', 'apax']
        
        if field1 in accepted_field1 :
            if field2 in accepted_field2 :
                if start is not None and end is not None :
                    data = get_cooc(corpus=corpus,field1=field1, field2=field2, start=start, end=end, apax=apax)
                else:
                    data = get_cooc(corpus=corpus,field1=field1, field2=field2, apax=apax)
                if format_ == 'json':
                    return JsonHttpResponse(data)
        else:
            return JsonHttpResponse({
                'Warning USAGE' : 'One field for each range:'
                , 'field1' : accepted_field1
                , 'field2' : accepted_field2
                , 'options': options
                })
