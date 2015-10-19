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
        '''
        field1 = request.GET.get('field1', 'ngrams')
        field2 = request.GET.get('field2', 'ngrams')
        format_   =  request.GET.get('format', 'json')
        type_    = request.GET.get('type', 'node_link')
        

        corpus = session.query(Node).filter(Node.id==corpus_id).first()
        
        accepted_field1 = ['ngrams', 'journal', 'source', 'authors']
        accepted_field2 = ['ngrams',]
        
        if field1 in accepted_field1 :
            if field2 in accepted_field2 :
                data = get_cooc(corpus=corpus,field1=field1, field2=field2)
                if format_ == 'json':
                    return JsonHttpResponse(data)
        else:
            return JsonHttpResponse({
                'Warning USAGE' : 'One field for each range:'
                , 'field1' : accepted_field1
                , 'field2' : accepted_field2
                })
