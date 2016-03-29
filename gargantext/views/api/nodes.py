
from gargantext.models          import Node, Ngram, NodeNgram, NodeNodeNgram
from gargantext.constants       import NODETYPES
from gargantext.util.db         import session, delete, func
from gargantext.util.db_cache   import cache, or_
from gargantext.util.validation import validate
from gargantext.util.http       import ValidationException, APIView \
                                     , get_parameters, JsonHttpResponse


from collections import defaultdict

_node_available_fields = ['id', 'parent_id', 'name', 'typename', 'hyperdata', 'ngrams']
_node_default_fields = ['id', 'parent_id', 'name', 'typename']
_node_available_types = NODETYPES


def _query_nodes(request, node_id=None):
    user = cache.User[request.user.id]
    # parameters validation
    parameters = get_parameters(request)
    parameters = validate(parameters, {'type': dict, 'items': {
        'pagination_limit': {'type': int, 'default': 10},
        'pagination_offset': {'type': int, 'default': 0},
        'fields': {'type': list, 'default': _node_default_fields, 'items': {
            'type': str, 'range': _node_available_fields,
        }},
        # optional filtering parameters
        'types': {'type': list, 'required': False, 'items': {
            'type': str, 'range': _node_available_types,
        }},
        'parent_id': {'type': int, 'required': False},
    }})
    # start the query
    query = user.nodes()
    # filter by id
    if node_id is not None:
        query = query.filter(Node.id == node_id)
    # filter by type
    if 'types' in parameters:
        query = query.filter(Node.typename.in_(parameters['types']))
    # filter by parent
    if 'parent_id' in parameters:
        query = query.filter(Node.parent_id == parameters['parent_id'])
    # count
    count = query.count()
    # order
    query = query.order_by(Node.hyperdata['publication_date'], Node.id)
    # paginate the query
    if parameters['pagination_limit'] == -1:
        query = query[parameters['pagination_offset']:]
    else:
        query = query[
            parameters['pagination_offset'] :
            parameters['pagination_limit']
        ]
    # return the result!
    return parameters, query, count


class NodeListResource(APIView):

    def get(self, request):
        """Displays the list of nodes corresponding to the query.
        """
        parameters, query, count = _query_nodes(request)
        return JsonHttpResponse({
            'parameters': parameters,
            'count': count,
            'records': [
                {field: getattr(node, field) for field in parameters['fields']}
                for node in query
            ]
        })

    
    def post(self, request):
        """Create a new node.
        NOT IMPLEMENTED
        """


    def delete(self, request):
        """Removes the list of nodes corresponding to the query.
        TODO : Should be a delete method!
        """
        parameters = get_parameters(request)
        parameters = validate(parameters, {'ids': list} )
        try :
            node_ids = [int(n) for n in parameters['ids'].split(',')]
        except :
            raise ValidationException('"ids" needs integers separated by comma.')

        result = session.execute(
            delete(Node).where(Node.id.in_(node_ids))
        )
        session.commit()

        return JsonHttpResponse({'deleted': result.rowcount})

class NodeListHaving(APIView):
    '''
    Gives a list of nodes according to its score which is related
    to some specific ngrams.
    TODO: implement other options (offset)

    Simple implementation:
    Takes IDs of corpus and ngram and returns list of relevent documents in json format
    according to TFIDF score (order is decreasing).


    '''
    def get(self, request, corpus_id):
        parameters = get_parameters(request)
        parameters = validate(parameters, {'score': str, 'ngram_ids' : list} )
        
        try :
            ngram_ids = [int(n) for n in parameters['ngram_ids'].split(',')]
        except :
            raise ValidationException('"ngram_ids" needs integers separated by comma.')

        limit=5
        nodes_list = []
        
        corpus = session.query(Node).filter(Node.id==corpus_id).first()
        
        tfidf_id  = ( session.query( Node.id )
                        .filter( Node.typename  == "TFIDF-CORPUS"
                               , Node.parent_id == corpus.id
                               )
                        .first()
                )

        
        tfidf_id = tfidf_id[0]
        print(tfidf_id)
        # request data
        nodes_query = (session
            .query(Node, func.sum(NodeNodeNgram.score))
            .join(NodeNodeNgram, NodeNodeNgram.node2_id == Node.id)
            .filter(NodeNodeNgram.node1_id == tfidf_id)
            .filter(Node.typename == 'DOCUMENT', Node.parent_id== corpus.id)
            .filter(or_(*[NodeNodeNgram.ngram_id==ngram_id for ngram_id in ngram_ids]))
            .group_by(Node)
            .order_by(func.sum(NodeNodeNgram.score).desc())
            .limit(limit)
        )
        # print("\n")
        # print("in TFIDF:")
        # print("\tcorpus_id:",corpus_id)
        # convert query result to a list of dicts
#         if nodes_query is None:
#             print("TFIDF error, juste take sums")
#             nodes_query = (session
#                 .query(Node, func.sum(NodeNgram.weight))
#                 .join(NodeNgram, NodeNgram.node_id == Node.id)
#                 .filter(Node.parent_id == corpus_id)
#                 .filter(Node.typename == 'DOCUMENT')
#                 .filter(or_(*[NodeNgram.ngram_id==ngram_id for ngram_id in ngram_ids]))
#                 .group_by(Node)
#                 .order_by(func.sum(NodeNgram.weight).desc())
#                 .limit(limit)
#             )
        for node, score in nodes_query:
            print(node,score)
            print("\t corpus:",corpus_id,"\t",node.name)
            node_dict = {
                'id': node.id,
                'score': score,
            }
            for key in ('title', 'publication_date', 'journal', 'authors', 'fields'):
                if key in node.hyperdata:
                    node_dict[key] = node.hyperdata[key]
            nodes_list.append(node_dict)

        return JsonHttpResponse(nodes_list)



class NodeResource(APIView):

    def get(self, request, node_id):
        parameters, query, count = _query_nodes(request, node_id)
        if not len(query):
            raise Http404()
        node = query[0]
        return JsonHttpResponse({
            field: getattr(node, field) for field in parameters['fields']
        })

    def delete(self, request, node_id):
        parameters, query, count = _query_nodes(request, node_id)
        if not len(query):
            raise Http404()
        result = session.execute(
            delete(Node).where(Node.id == node_id)
        )
        session.commit()
        return JsonHttpResponse({'deleted': result.rowcount})


class CorpusFacet(APIView):
    """Loop through a corpus node's docs => do counts by a hyperdata field
        (url: /api/nodes/<node_id>/facets?hyperfield=<journal>)
    """
    # - old url: '^project/(\d+)/corpus/(\d+)/journals/journals.json$',
    # - old view: tests.ngramstable.views.get_journals_json()
    # - now generalized for various hyperdata field:
    #    -> journal
    #    -> publication_year
    #    -> rubrique
    #    -> language...

    def get(self, request, node_id):
        # check that the node is a corpus
        #   ? faster from cache than: corpus = session.query(Node)...
        corpus = cache.Node[node_id]
        if corpus.typename != 'CORPUS':
            raise ValidationException(
                "Only nodes of type CORPUS can accept facet queries" +
                " (but this node has type %s)..." % corpus.typename
            )
        else:
            self.corpus = corpus

        # check that the hyperfield parameter makes sense
        _facet_available_subfields = [
            'journal', 'publication_year', 'rubrique',
            'language_iso2', 'language_iso3', 'language_name'
        ]
        parameters = get_parameters(request)

        # validate() triggers an info message if subfield not in range
        parameters = validate(parameters, {'type': dict, 'items': {
            'hyperfield': {'type': str, 'range': _facet_available_subfields}
            }})

        subfield = parameters['hyperfield']

        # do the aggregated sum
        (xcounts, total) = self._ndocs_by_facet(subfield)

        # response
        return JsonHttpResponse({
            'doc_count' : total,
            'by': { subfield: xcounts }
        })

    def _ndocs_by_facet(self, subfield='journal'):
        """for example on 'journal'
         xcounts = {'j good sci' : 25, 'nature' : 32, 'j bla bla' : 1... }"""

        xcounts = defaultdict(int)
        total = 0
        for doc in self.corpus.children(typename='DOCUMENT'):
            if subfield in doc.hyperdata:
                xcounts[doc.hyperdata[subfield]] += 1
            else:
                xcounts["_NA_"] += 1

            total += 1

        # the counts below could also be memoized
        #  // if subfield not in corpus.aggs:
        #  //     corpus.aggs[subfield] = xcounts
        return (xcounts, total)



