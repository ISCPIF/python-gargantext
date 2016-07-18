#from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from gargantext.util.db      import session
from gargantext.models.nodes import Node
from graph.graph             import get_graph
from gargantext.util.http    import APIView, APIException\
                                  , JsonHttpResponse, requires_auth

from gargantext.constants    import graph_constraints
from traceback import format_tb

def compress_graph(graphdata):
    """
    graph data is usually a dict with 2 slots:
      "nodes": [{"id":4103, "type":"terms", "attributes":{"clust_default": 0}, "size":29, "label":"regard"},...]
      "links": [{"t": 998,"s": 768,"w": 0.0425531914893617},...]

    To send this data over the net, this function can reduce a lot of its size:
      - keep less decimals for float value of each link's weight
      - use shorter names for node properties (eg: s/clust_default/cl/)

    result format:
        "nodes": [{"id":4103, "at":{"cl": 0}, "s":29, "lb":"regard"},...]
        "links": [{"t": 998,"s": 768,"w": 0.042},...]
    """
    for link in graphdata['links']:
        link['w'] = format(link['w'], '.3f')   # keep only 3 decimals

    for node in graphdata['nodes']:
        node['lb'] = node['label']
        del node['label']

        node['at'] = node['attributes']
        del node['attributes']

        node['at']['cl'] = node['at']['clust_default']
        del node['at']['clust_default']

        node['s'] = node['size']
        del node['size']

        if node['type'] == "terms":
            # its the default type for our format: so we don't need it
            del node['type']
        else:
            node['t'] = node['type']
            del node['type']

    return graphdata

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
        cooc_id      = request.GET.get     ('cooc_id'   , None         )

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
                # todo add as an error msg ?
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
                # todo add as an error msg ?
                raise ValueError("GROUPLIST node needed for cooccurrences")


        # Check the options
        accepted_field1 = ['ngrams', 'journal', 'source', 'authors']
        accepted_field2 = ['ngrams',                               ]
        options         = ['start', 'end', 'threshold', 'distance', 'cooc_id' ]


        try:
            # Test params
            if (field1 in accepted_field1) and (field2 in accepted_field2):
                if start is not None and end is not None :
                    data = get_graph( corpus=corpus, cooc_id = cooc_id
                                  #, field1=field1           , field2=field2
                                   , mapList_id = mapList_id , groupList_id = groupList_id
                                   , start=start             , end=end
                                   , threshold =threshold    , distance=distance
                                   )
                else:
                    data = get_graph( corpus = corpus, cooc_id = cooc_id
                                  #, field1=field1, field2=field2
                                   , mapList_id = mapList_id , groupList_id = groupList_id
                                   , threshold  = threshold
                                   , distance   = distance
                                   , bridgeness = bridgeness
                                   )


                # Test data length
                if len(data['nodes']) > 1 and len(data['links']) > 1 :
                    # normal case --------------------------------
                    if format_ == 'json':
                        return JsonHttpResponse(
                                 compress_graph(data),
                                 status=200
                               )
                    # --------------------------------------------
                
                elif len(data['nodes']) == 0 and len(data['links']) == 2 :
                    # async data case
                    return JsonHttpResponse({
                        'msg': '''Your corpus is too small.
                                  Add more documents (more than %d documents) 
                                  in order to get a graph.

                                  You can manage your corpus here:
                                  http://%sgargantext.org/projects/%d/
                                  ''' % (graph_constraints['corpusMin'], "dev.", corpus.parent_id),
                        }, status=400)
                
                elif len(data['nodes']) == 0 and len(data['links']) == 3 :
                    # async data case
                    return JsonHttpResponse({
                        'msg': '''Your map list is too small.
                                  Add some terms (more than %d terms) 
                                  in order to get a graph.

                                  You can manage your map terms here:
                                  http://%sgargantext.org/projects/%d/corpora/%d/terms
                                  ''' % (graph_constraints['mapList'], "dev.", corpus.parent_id, corpus.id),
                        }, status=400)



                elif len(data['nodes']) == 0 and len(data['links']) == 1 :
                    # async data case
                    return JsonHttpResponse({
                        'msg': '''Async graph generation
                                  Wait a while and discover your graph 
                                  http://%sgargantext.org/projects/%d/corpora/%d/myGraph
                                  ''' % ("dev.", corpus.parent_id, corpus.id),
                        }, status=400)

                else:
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
