
from gargantext.models          import Node, Ngram, NodeNgram, NodeNodeNgram, NodeNode
from gargantext.constants       import NODETYPES, DEFAULT_N_DOCS_HAVING_NGRAM
from gargantext.util.db         import session, delete, func, bulk_insert
from gargantext.util.db_cache   import cache, or_
from gargantext.util.validation import validate
from gargantext.util.http       import ValidationException, APIView \
                                     , get_parameters, JsonHttpResponse, Http404\
                                     , HttpResponse


from collections import defaultdict

import csv

_node_available_fields = ['id', 'parent_id', 'name', 'typename', 'hyperdata', 'ngrams']
_node_default_fields = ['id', 'parent_id', 'name', 'typename']
_node_available_types = NODETYPES

#_hyperdata_available_fields = ['title', 'resourcetype']
#_node_available_formats = ['json', 'csv', 'bibex']


def _query_nodes(request, node_id=None):
    user = cache.User[request.user.id]
    # parameters validation
    parameters = get_parameters(request)
    parameters = validate(parameters, {'type': dict, 'items': {
        'formated': {'type': str, 'required' : False, 'default': 'json'},
#        'hyperdata': {'type': list, 'default' : _hyperdata_available_fields, 'items': {
#            'type': str, 'range' : _node_available_fields,
#        }},
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

        if parameters['formated'] == 'json':
            return JsonHttpResponse({
                'parameters': parameters,
                'count': count,
                'records': [
                    { field: getattr(node, field) for field in parameters['fields'] }
                    for node in query
                ]
            })

        elif parameters['formated'] == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="Gargantext_Corpus.csv"'

            writer = csv.writer(response, delimiter='\t', quoting=csv.QUOTE_MINIMAL)

            keys =  [ 'title'   , 'journal'
                    , 'publication_year', 'publication_month', 'publication_day'
                    , 'abstract', 'authors']

            writer.writerow(keys)

            for node in query:
                data = list()
                for key in keys:
                    try:
                        data.append(node.hyperdata[key])
                    except:
                        data.append("")
                writer.writerow(data)

            return response



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

    2016-09: add total counts to output json
    '''
    def get(self, request, corpus_id):
        parameters = get_parameters(request)
        parameters = validate(parameters, {'score': str, 'ngram_ids' : list} )

        try :
            ngram_ids = [int(n) for n in parameters['ngram_ids'].split(',')]
        except :
            raise ValidationException('"ngram_ids" needs integers separated by comma.')

        limit = DEFAULT_N_DOCS_HAVING_NGRAM
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
        )

        # get the total count before applying limit
        nodes_count = nodes_query.count()

        # now the query with the limit
        nodes_results_query = (nodes_query
                                .order_by(func.sum(NodeNodeNgram.score).desc())
                                .limit(limit)
                            )

        for node, score in nodes_results_query:
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

        return JsonHttpResponse({
                                    'count': nodes_count,
                                    'records': nodes_list
                                })



class NodeResource(APIView):

    # TODO either real authentification test or remove check on user.id
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



class CorpusFavorites(APIView):
    """Retrieve/update/delete one or several docs from a corpus associated favs
        (url: GET  /api/nodes/<corpus_id>/favorites)
        => lists all favorites
        (url: GET  /api/nodes/<corpus_id>/favorites?docs[]=doc1,doc2)
        => checks for each doc if it is in favorites
        (url: DEL  /api/nodes/<corpus_id>/favorites?docs[]=doc1,doc2)
        => removes each doc from favorites
        (url: PUT /api/nodes/<corpus_id>/favorites?docs[]=doc1,doc2)
        => add each doc to favorites
    """

    def _get_fav_node(self, corpus_id):
        """
        NB: fav_node can be None if no node is defined

        this query could be faster if we didn't check that corpus_id is a CORPUS
        ie: session.query(Node)
            .filter(Node.parent_id==corpus_id)
            .filter(Node.typename =='FAVORITES')
        """
        corpus = cache.Node[corpus_id]
        if corpus.typename != 'CORPUS':
            raise ValidationException(
                "Only nodes of type CORPUS can accept favorites queries" +
                " (but this node has type %s)..." % corpus.typename)
        else:
            self.corpus = corpus
        fav_node = self.corpus.children('FAVORITES').first()

        return fav_node

    def get(self, request, corpus_id):
        """
        2 possibilities with/without param

        1) GET http://localhost:8000/api/nodes/2/favorites
        (returns the full list of fav docs within corpus 2)

        2) GET http://localhost:8000/api/nodes/2/favorites?docs=53,54
        (will test if docs 53 and 54 are among the favorites of corpus 2)
        (returns the intersection of fav docs with [53,54])
        """
        fav_node = self._get_fav_node(corpus_id)

        req_params = validate(
            get_parameters(request),
            {'docs': list, 'default': ""}
        )

        response = {}

        if fav_node == None:
            response = {
                'warning':'No favorites node is defined for this corpus (\'%s\')'
                        % self.corpus.name ,
                'favdocs':[]
                }
        elif 'docs' not in req_params:
            # each docnode associated to the favnode of this corpusnode
            q = (session
                    .query(NodeNode.node2_id)
                    .filter(NodeNode.node1_id==fav_node.id))
            all_doc_ids = [row.node2_id for row in q.all()]
            response = {
                'favdocs': all_doc_ids
            }
        else:
            nodeids_to_check = [int(did) for did in req_params['docs'].split(',')]

            # each docnode from the input list, if it is associated to the favnode
            q = (session
                    .query(NodeNode.node2_id)
                    .filter(NodeNode.node1_id==fav_node.id)
                    .filter(NodeNode.node2_id.in_(nodeids_to_check)))
            present_doc_ids = [row.node2_id for row in q.all()]
            absent_doc_ids = [did for did in nodeids_to_check if did not in present_doc_ids]
            response = {
                'favdocs': present_doc_ids,
                'missing': absent_doc_ids
            }

        return JsonHttpResponse(response)

    def delete(self, request, corpus_id):
        """
        DELETE http://localhost:8000/api/nodes/2/favorites?docs=53,54
        (will delete docs 53 and 54 from the favorites of corpus 2)
        """
        if not request.user.is_authenticated():
            # can't use @requires_auth because of positional 'self' within class
            return HttpResponse('Unauthorized', status=401)

        # user is ok
        fav_node = self._get_fav_node(corpus_id)

        response = {}

        if fav_node == None:
            response = {
                'warning':'No favorites node is defined for this corpus (\'%s\')'
                        % self.corpus.name ,
                'count_removed': 0
                }
        else:
            req_params = validate(
                get_parameters(request),
                {'docs': list, 'default': ""}
            )
            nodeids_to_delete = [int(did) for did in req_params['docs'].split(',')]

            # it deletes from favourites but not from DB
            result = session.execute(
                delete(NodeNode)
                    .where(NodeNode.node1_id == fav_node.id)
                    .where(NodeNode.node2_id.in_(nodeids_to_delete))
            )
            session.commit()
            response = {'count_removed': result.rowcount}

        return JsonHttpResponse(response)

    def put(self, request, corpus_id, check_each_doc=True):
        if not request.user.is_authenticated():
            # can't use @requires_auth because of positional 'self' within class
            return HttpResponse('Unauthorized', status=401)

        # user is ok
        fav_node = self._get_fav_node(corpus_id)

        response = {}

        if fav_node == None:
            response = {
                'warning':'No favorites node is defined for this corpus (\'%s\')'
                        % self.corpus.name ,
                'count_added':0
                }
        else:
            req_params = validate(
                get_parameters(request),
                {'docs': list, 'default': ""}
            )
            nodeids_to_add = [int(did) for did in req_params['docs'].split(',')]

            if check_each_doc:
                # verification que ce sont bien des documents du bon corpus
                # un peu long => désactiver par défaut ?
                known_docs_q = (session
                                .query(Node.id)
                                .filter(Node.parent_id==corpus_id)
                                .filter(Node.typename=='DOCUMENT')
                            )
                lookup = {known_doc.id:True for known_doc in known_docs_q.all()}
                # debug
                # print("lookup hash", lookup)
                rejected_list = []
                for doc_node_id in nodeids_to_add:
                    if (doc_node_id not in lookup):
                        rejected_list.append(doc_node_id)
                if len(rejected_list):
                    raise ValidationException(
                        "Error on some requested docs: %s (Only nodes of type 'doc' AND belonging to corpus %i can be added to favorites.)"
                            % (str(rejected_list), int(corpus_id)))

            # add them
            bulk_insert(
                NodeNode,
                ('node1_id', 'node2_id', 'score'),
                ((fav_node.id, doc_node_id, 1.0 ) for doc_node_id in nodeids_to_add)
            )

            # todo count really added (here: counts input param not result)
            response = {'count_added': len(nodeids_to_add)}

        return JsonHttpResponse(response)



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
            'language_iso2', 'language_iso3', 'language_name',
            'authors'
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
