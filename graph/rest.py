#from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from gargantext.util.db      import session
from gargantext.models.nodes import Node
from graph.graph             import get_graph
from graph.utils             import compress_graph, format_html
from gargantext.util.http    import APIView, APIException\
                                  , JsonHttpResponse, requires_auth

from gargantext.constants    import graph_constraints
from traceback import format_tb

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

        if not request.user.is_authenticated():
            # can't use @requires_auth because of positional 'self' within class
            return HttpResponse('Unauthorized', status=401)

        # Get the node we are working with
        corpus = session.query(Node).filter(Node.id==corpus_id).first()

        # Get all the parameters in the URL
        cooc_id      = request.GET.get     ('cooc_id'   , None         )
        saveOnly     = request.GET.get     ('saveOnly'  , None         )

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

        # Get default map List of corpus
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


        # Declare accepted fields
        accepted_field1 = ['ngrams', 'journal', 'source', 'authors']
        accepted_field2 = ['ngrams',                               ]
        options         = ['start', 'end', 'threshold', 'distance', 'cooc_id' ]


        try:
            # Check if parameters are accepted
            if (field1 in accepted_field1) and (field2 in accepted_field2):
                data = get_graph( corpus=corpus, cooc_id = cooc_id
                               , field1=field1           , field2=field2
                               , mapList_id = mapList_id , groupList_id = groupList_id
                               , start=start             , end=end
                               , threshold =threshold    
                               , distance=distance       , bridgeness=bridgeness
                               , saveOnly=saveOnly
                               )


                # data :: Either (Dic Nodes Links) (Dic State Length)

                # data_test :: Either String Bool
                data_test = data.get("state", True)

                if data_test is True:
                    # normal case --------------------------------
                    if format_ == 'json':
                        return JsonHttpResponse(
                                 compress_graph(data),
                                 status=200
                               )
                    # --------------------------------------------

                else:
                    # All other cases (more probable are higher in the if list)

                    if data["state"] == "saveOnly":
                        # async data case
                        link = "http://%s/projects/%d/corpora/%d/myGraphs" % (request.get_host(), corpus.parent_id, corpus.id)
                        return JsonHttpResponse({
                            'msg': '''Your graph is saved:

                                      %s
                                      ''' % format_html(link),
                            }, status=200)

                    elif data["state"] == "corpusMin":
                        # async data case
                        link = "http://%s/projects/%d/" % (request.get_host(), corpus.parent_id)
                        return JsonHttpResponse({
                            'msg': '''Problem: your corpus is too small (only %d documents).

                                      Solution: Add more documents (more than %d documents)
                                      in order to get a graph.

                                      You can manage your corpus here:
                                      %s
                                      ''' % ( data["length"]
                                            , graph_constraints['corpusMin']
                                            , format_html(link)
                                            ),
                            }, status=400)

                    elif data["state"] == "mapListError":
                        # async data case
                        link = 'http://%s/projects/%d/corpora/%d/terms' % (request.get_host(), corpus.parent_id, corpus.id)
                        return JsonHttpResponse({
                            'msg': '''Problem: your map list is too small (currently %d terms).

                                      Solution: Add some terms (more than %d terms)
                                      in order to get a graph.

                                      You can manage your map terms here:
                                      %s
                                      ''' % ( data["length"]
                                            , graph_constraints['mapList']
                                            , format_html(link)
                                            ),
                            }, status=400)


                    elif data["state"] == "corpusMax":
                        # async data case
                        link = 'http://%s/projects/%d/corpora/%d/myGraphs' % (request.get_host(), corpus.parent_id, corpus.id)
                        return JsonHttpResponse({
                            'msg': '''Warning: Async graph generation since your corpus is
                                      big (about %d documents).

                                      Wait a while and discover your graph very soon.

                                      Click on the link below and see your current graph
                                      processing on top of the list:

                                      %s
                                      ''' % (data["length"], format_html(link)),
                            }, status=200)



                    else :
                       return JsonHttpResponse({
                            'msg': '''Programming error.''',
                            }, status=400)


            elif len(data["nodes"]) < 2 and len(data["links"]) < 2:
                # empty data case
                return JsonHttpResponse({
                    'msg': '''Empty graph warning
                              No cooccurences found in this corpus for the words of this maplist
                              (maybe add more terms to the maplist or increase the size of your
                              corpus ?)''',
                    }, status=400)

            else:
                # parameters error case
                return JsonHttpResponse({
                    'msg': '''Usage warning
                              Please choose only one field from each range:
                                - "field1": %s
                                - "field2": %s
                                - "options": %s''' % (accepted_field1, accepted_field2, options)
                    }, status=400)

        # for any other errors that we forgot to test
        except Exception as error:
            print(error)
            return JsonHttpResponse({
                'msg' : 'Unknown error (showing the trace):\n%s' % "\n".join(format_tb(error.__traceback__))
                }, status=400)
