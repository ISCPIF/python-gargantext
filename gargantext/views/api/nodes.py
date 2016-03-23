from gargantext.util.http import *
from gargantext.util.db import *
from gargantext.util.db_cache import *
from gargantext.models import *
from gargantext.constants import *

from gargantext.util.validation import validate

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
        WARNING! THIS IS TOTALLY UNTESTED!!!!!
        """
        parameters, query, count = _query_nodes(request)
        query.delete()
        session.commit()
        return JsonHttpResponse({
            'parameters': parameters,
            'count': count,
        }, 200)


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
        from sqlalchemy import delete
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


class CorpusGraph(APIView):
    '''
    Generate a graph
    '''
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

        # do_cooc
        # do_distance

        # response
        return JsonHttpResponse({
            'doc_count' : total,
            'by': { subfield: xcounts }
        })


