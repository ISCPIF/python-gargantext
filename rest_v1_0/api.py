from django.http import HttpResponse, Http404
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse

from sqlalchemy import text, distinct, or_,not_
from sqlalchemy.sql import func, desc
from sqlalchemy.orm import aliased

import datetime
import copy

from gargantext_web.views import move_to_trash
from gargantext_web.db import get_session, cache, Node, NodeNgram, NodeNgramNgram, NodeNodeNgram, Ngram, Hyperdata, Node_Ngram\
        , NodeType, Node_Hyperdata
from gargantext_web.validation import validate, ValidationException
from node import models

def DebugHttpResponse(data):
    return HttpResponse('<html><body style="background:#000;color:#FFF"><pre>%s</pre></body></html>' % (str(data), ))

import json
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()[:19] + 'Z'
        else:
            return super(self.__class__, self).default(obj)
json_encoder = JSONEncoder(indent=4)
def JsonHttpResponse(data, status=200):
    return HttpResponse(
        content      = json_encoder.encode(data),
        content_type = 'application/json; charset=utf-8',
        status       = status
    )
Http400 = SuspiciousOperation
Http403 = PermissionDenied

import csv
def CsvHttpResponse(data, headers=None, status=200):
    response = HttpResponse(
        content_type = "text/csv",
        status       = status
    )
    writer = csv.writer(response, delimiter=',')
    if headers:
        writer.writerow(headers)
    for row in data:
        writer.writerow(row)
    return response

_ngrams_order_columns = {
    "frequency" : "-count",
    "alphabetical" : "terms"
}


from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import APIException as _APIException

class APIException(_APIException):
    def __init__(self, message, code=500):
        self.status_code = code
        self.detail = message

session = get_session()

_operators_dict = {
    "=":                lambda field, value: (field == value),
    "!=":               lambda field, value: (field != value),
    "<":                lambda field, value: (field < value),
    ">":                lambda field, value: (field > value),
    "<=":               lambda field, value: (field <= value),
    ">=":               lambda field, value: (field >= value),
    "in":               lambda field, value: (or_(*tuple(field == x for x in value))),
    "contains":         lambda field, value: (field.contains(value)),
    "doesnotcontain":  lambda field, value: (not_(field.contains(value))),
    "startswith":       lambda field, value: (field.startswith(value)),
}
_hyperdata_list = [
    hyperdata
    for hyperdata in session.query(Hyperdata).order_by(Hyperdata.name)
]
_hyperdata_dict = {
    hyperdata.name: hyperdata
    for hyperdata in _hyperdata_list
}

from rest_framework.decorators import api_view

@api_view(('GET',))
def Root(request, format=None):
    return Response({
        'users': reverse('user-list', request=request, format=format),
        'snippets': reverse('snippet-list', request=request, format=format)
    })

session.remove()

class NodesChildrenNgrams(APIView):

    def get(self, request, node_id):
        session = get_session()
        
        # query ngrams
        ParentNode = aliased(Node)
        
        ngrams_query = (session
            .query(Ngram.terms, func.sum(Node_Ngram.weight).label('count'))
            .join(Node_Ngram, Node_Ngram.ngram_id == Ngram.id)
            .join(Node, Node.id == Node_Ngram.node_id)
            .filter(Node.parent_id == node_id)
            .group_by(Ngram.terms)
            # .group_by(Ngram)
            .order_by(func.sum(Node_Ngram.weight).desc(), Ngram.terms)
        )
        # filters
        if 'startwith' in request.GET:
            ngrams_query = ngrams_query.filter(Ngram.terms.startswith(request.GET['startwith']))
        if 'contain' in request.GET:
            ngrams_query = ngrams_query.filter(Ngram.terms.contains(request.GET['contain']))
        #if 'doesnotcontain' in request.GET:
        #    ngrams_query = ngrams_query.filter(not_(Ngram.terms.contains(request.GET['doesnotcontain'])))
        # pagination
        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('limit', 20))
        total = ngrams_query.count()
        # return formatted result
        return JsonHttpResponse({
            'pagination': {
                'offset': offset,
                'limit': limit,
                'total': total,
            },
            'data': [
                {
                    # 'id': ngram.id,
                    'terms': ngram.terms,
                    'count': ngram.count,
                }
                for ngram in ngrams_query[offset : offset+limit]
            ],
        })
        
        session.remove()

class NodesChildrenNgramsIds(APIView):

    def get(self, request, node_id):
        session = get_session()
        
        # query ngrams
        ParentNode = aliased(Node)
        ngrams_query = (session
            .query(Node.id, func.sum(Node_Ngram.weight).label('count'))
            .join(Node_Ngram, Node_Ngram.node_id == Node.id)
            .join(Ngram, Ngram.id == Node_Ngram.ngram_id)
            .filter(Node.parent_id == node_id)
            .filter(Node.type_id == cache.NodeType['Document'].id)
            .group_by(Node.id)
            # .group_by(Ngram)
            .order_by(func.sum(Node_Ngram.weight).desc())
        )
        # filters
        if 'startwith' in request.GET:
            ngrams_query = ngrams_query.filter(Ngram.terms.startswith(request.GET['startwith']))
        if 'contain' in request.GET:
            ngrams_query = ngrams_query.filter(Ngram.terms.contains(request.GET['contain']))
        #if 'doesnotcontain' in request.GET:
        #    ngrams_query = ngrams_query.filter(not_(Ngram.terms.contains(request.GET['doesnotcontain'])))
        # pagination
        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('limit', 20))
        total = ngrams_query.count()
        # return formatted result
        return JsonHttpResponse({
            'pagination': {
                'offset': offset,
                'limit': limit,
                'total': total,
            },
            'data': [
                {
                    'id': node,
                    'count': count
                }
                for node, count in ngrams_query[offset : offset+limit]
            ],
        })
        
        session.remove()


from gargantext_web.db import get_or_create_node

class Ngrams(APIView):
    def get(self, request, node_id):
        session = get_session()
        
        # query ngrams
        ParentNode = aliased(Node)
        corpus = session.query(Node).filter(Node.id==node_id).first()
        group_by = []
        results   = ['id', 'terms']

        ngrams_query = (session
            .query(Ngram.id, Ngram.terms)
            .join(Node_Ngram, Node_Ngram.ngram_id == Ngram.id)
            .join(Node, Node.id == Node_Ngram.node_id)
        )

        # get the scores
        if 'tfidf' in request.GET['score']:
            Tfidf = aliased(NodeNodeNgram)
            tfidf_id = get_or_create_node(nodetype='Tfidf (global)', corpus=corpus).id
            ngrams_query = (ngrams_query.add_column(Tfidf.score.label('tfidf'))
                                        .join(Tfidf, Tfidf.ngram_id == Ngram.id)
                                        .filter(Tfidf.nodex_id == tfidf_id)
                            )
            group_by.append(Tfidf.score)
            results.append('tfidf')

        if 'cvalue' in request.GET['score']:
            Cvalue = aliased(NodeNodeNgram)
            cvalue_id = get_or_create_node(nodetype='Cvalue', corpus=corpus).id
            ngrams_query = (ngrams_query.add_column(Cvalue.score.label('cvalue'))
                                        .join(Cvalue, Cvalue.ngram_id == Ngram.id)
                                        .filter(Cvalue.nodex_id == cvalue_id)
                            )
            group_by.append(Cvalue.score)
            results.append('cvalue')


        if 'specificity' in request.GET['score']:
            Spec = aliased(NodeNodeNgram)
            spec_id = get_or_create_node(nodetype='Specificity', corpus=corpus).id
            ngrams_query = (ngrams_query.add_column(Spec.score.label('specificity'))
                                        .join(Spec, Spec.ngram_id == Ngram.id)
                                        .filter(Spec.nodex_id == spec_id)
                            )
            group_by.append(Spec.score)
            results.append('specificity')


        if request.GET.get('order', False) == 'cvalue':
            ngrams_query = ngrams_query.order_by(desc(Cvalue.score))
        elif request.GET.get('order', False) == 'tfidf':
            ngrams_query = ngrams_query.order_by(desc(Tfidf.score))
        elif request.GET.get('order', False) == 'specificity':
            ngrams_query = ngrams_query.order_by(desc(Spec.score))

        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('limit', 20))

        ngrams_query = (ngrams_query.filter(Node.parent_id == node_id)
                        .group_by(Ngram.id, Ngram.terms, *group_by)
                        )

        if request.GET.get('ngram_id', False) != False:
            ngram_id = int(request.GET['ngram_id'])
            Group = aliased(NodeNgramNgram)
            group_id = get_or_create_node(nodetype='Group', corpus=corpus).id
            ngrams_query = (ngrams_query.join(Group, Group.ngramx_id == ngram_id )
                                        .filter(Group.node_id == group_id)
                                        .filter(Group.ngramx_id == ngram_id)
                            )

        # filters by list type (soon list_id to factorize it in javascript)
        list_query = request.GET.get('list', 'miam')
        if list_query == 'miam':
            Miam = aliased(NodeNgram)
            miam_id = get_or_create_node(nodetype='MiamList', corpus=corpus).id
            ngrams_query = (ngrams_query.join(Miam, Miam.ngram_id == Ngram.id )
                                        .filter(Miam.node_id == miam_id)
                            )
        elif list_query == 'stop':
            Stop = aliased(NodeNgram)
            stop_id = get_or_create_node(nodetype='StopList', corpus=corpus).id
            ngrams_query = (ngrams_query.join(Stop, Stop.ngram_id == Ngram.id )
                                        .filter(Stop.node_id == stop_id)
                            )
        elif list_query == 'map':
        # ngram could be in ngramx_id or ngramy_id
            CoocX = aliased(NodeNgramNgram)
            CoocY = aliased(NodeNgramNgram)
            cooc_id = get_or_create_node(nodetype='Cooccurrence', corpus=corpus).id
            ngrams_query = (ngrams_query.join(CoocX, CoocX.ngramx_id == Ngram.id )
                                        .join(CoocY, CoocY.ngramy_id == Ngram.id)
                                        .filter(CoocX.node_id == cooc_id)
                                        .filter(CoocY.node_id == cooc_id)
                            )

        total = ngrams_query.count()

        # return formatted result
        return JsonHttpResponse({
            'pagination': {
                'offset': offset,
                'limit': limit,
                'total': total,
                          },
            'data': [
                        {
                            'id' : ngram.id
                            , 'terms' : ngram.terms
                            , 'tfidf' : ngram.tfidf
                            , 'cvalue': ngram.cvalue

                        } for ngram in ngrams_query[offset : offset+limit]
                # TODO : dict comprehension in list comprehension :
#                        { x : eval('ngram.' + x) for x in results
#                        } for ngram in ngrams_query[offset : offset+limit]

                    ],
                               })
        session.remove()
        

class NodesChildrenDuplicates(APIView):
    def _fetch_duplicates(self, request, node_id, extra_columns=None, min_count=1):
        session = get_session()
        
        # input validation
        if extra_columns is None:
            extra_columns = []
        if 'keys' not in request.GET:
            raise APIException('Missing GET parameter: "keys"', 400)
        keys = request.GET['keys'].split(',')
        # hyperdata retrieval
        hyperdata_query = (session
            .query(Hyperdata)
            .filter(Hyperdata.name.in_(keys))
        )
        # build query elements
        columns = []
        aliases = []
        for hyperdata in hyperdata_query:
            # aliases
            _Hyperdata = aliased(Hyperdata)
            _Node_Hyperdata = aliased(Node_Hyperdata)
            aliases.append(_Node_Hyperdata)
            # what shall we retrieve?
            columns.append(
                getattr(_Node_Hyperdata, 'value_' + hyperdata.type)
            )
        # build the query
        groups = list(columns)
        duplicates_query = (session
            .query(*(extra_columns + [func.count()] + columns))
            .select_from(Node)
        )
        for _Node_Hyperdata, hyperdata in zip(aliases, hyperdata_query):
            duplicates_query = duplicates_query.outerjoin(_Node_Hyperdata, _Node_Hyperdata.node_id == Node.id)
            duplicates_query = duplicates_query.filter(_Node_Hyperdata.hyperdata_id == hyperdata.id)
        duplicates_query = duplicates_query.filter(Node.parent_id == node_id)
        duplicates_query = duplicates_query.group_by(*columns)
        duplicates_query = duplicates_query.order_by(func.count().desc())
        duplicates_query = duplicates_query.having(func.count() > min_count)
        # and now, return it
        return duplicates_query
        
        session.remove()

    def get(self, request, node_id):
        # data to be returned
        duplicates = self._fetch_duplicates(request, node_id)
        # pagination
        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('limit', 10))
        total = duplicates.count()
        # response building
        return JsonHttpResponse({
            'pagination': {
                'offset': offset,
                'limit': limit,
                'total': total,
            },
            'data': [
                {
                    'count': duplicate[0],
                    'values': duplicate[1:],
                }
                for duplicate in duplicates[offset : offset+limit]
            ]
        })

    def delete(self, request, node_id):
        # get the minimum ID for each of the nodes sharing the same hyperdata
        kept_node_ids_query = self._fetch_duplicates(request, node_id, [func.min(Node.id).label('id')], 0)
        kept_node_ids = [kept_node.id for kept_node in kept_node_ids_query]
        # TODO with new orm
        duplicate_nodes = models.Node.objects.filter( parent_id=node_id ).exclude(id__in=kept_node_ids)
        # # delete the stuff
        # delete_query = (session
        #     .query(Node)
        #     .filter(Node.parent_id == node_id)
        #     .filter(~Node.id.in_(kept_node_ids))
        # )
        count = len(duplicate_nodes)
        for node in duplicate_nodes:
            print("deleting node ",node.id)
            move_to_trash(node.id)
        # print(delete_query)
        # # delete_query.delete(synchronize_session=True)
        # session.flush()
        return JsonHttpResponse({
            'deleted': count
        })

# retrieve metadata from a given list of parent node
def get_metadata(corpus_id_list):
    
    session = get_session()

    # query hyperdata keys
    ParentNode = aliased(Node)
    hyperdata_query = (session
        .query(Hyperdata)
        .join(Node_Hyperdata, Node_Hyperdata.hyperdata_id == Hyperdata.id)
        .join(Node, Node.id == Node_Hyperdata.node_id)
        .filter(Node.parent_id.in_(corpus_id_list))
        .group_by(Hyperdata)
    )

    # build a collection with the hyperdata keys
    collection = []
    for hyperdata in hyperdata_query:
        valuesCount = 0
        values = None

        # count values and determine their span
        values_count = None
        values_from = None
        values_to = None
        if hyperdata.type != 'text':
            value_column = getattr(Node_Hyperdata, 'value_' + hyperdata.type)
            node_hyperdata_query = (session
                .query(value_column)
                .join(Node, Node.id == Node_Hyperdata.node_id)
                .filter(Node.parent_id.in_(corpus_id_list))
                .filter(Node_Hyperdata.hyperdata_id == hyperdata.id)
                .group_by(value_column)
                .order_by(value_column)
            )
            values_count = node_hyperdata_query.count()
            # values_count, values_from, values_to = node_hyperdata_query.first()

        # if there is less than 32 values, retrieve them
        values = None
        if isinstance(values_count, int) and values_count <= 48:
            if hyperdata.type == 'datetime':
                values = [row[0].isoformat() for row in node_hyperdata_query.all()]
            else:
                values = [row[0] for row in node_hyperdata_query.all()]

        # adding this hyperdata to the collection
        collection.append({
            'key': hyperdata.name,
            'type': hyperdata.type,
            'values': values,
            'valuesFrom': values_from,
            'valuesTo': values_to,
            'valuesCount': values_count,
        })

    # give the result back
    return collection
    session.remove()

class ApiHyperdata(APIView):

    def get(self, request):
        corpus_id_list = list(map(int, request.GET['corpus_id'].split(',')))
        return JsonHttpResponse({
            'data': get_metadata(corpus_id_list),
        })


# retrieve ngrams from a given list of parent node
def get_ngrams(corpus_id_list):
    pass

class ApiNgrams(APIView):
    
    def get(self, request):

        # parameters retrieval and validation
        startwith = request.GET.get('startwith', '').replace("'", "\\'")

        # query ngrams
        ParentNode = aliased(Node)
        session = get_session()
        ngrams_query = (session
            .query(Ngram.terms, func.sum(Node_Ngram.weight).label('count'))
            .join(Node_Ngram, Node_Ngram.ngram_id == Ngram.id)
            .join(Node, Node.id == Node_Ngram.node_id)
            .group_by(Ngram.terms)
            # .group_by(Ngram)
            .order_by(func.sum(Node_Ngram.weight).desc(), Ngram.terms)
        )

        # filters
        if 'startwith' in request.GET:
            ngrams_query = ngrams_query.filter(Ngram.terms.startswith(request.GET['startwith']))
        if 'contain' in request.GET:
            ngrams_query = ngrams_query.filter(Ngram.terms.contains(request.GET['contain']))
        if 'corpus_id' in request.GET:
            corpus_id_list = list(map(int, request.GET.get('corpus_id', '').split(',')))
            if corpus_id_list and corpus_id_list[0]:
                ngrams_query = ngrams_query.filter(Node.parent_id.in_(corpus_id_list))

        # pagination
        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('limit', 20))
        total = ngrams_query.count()
        # return formatted result
        return JsonHttpResponse({
            'pagination': {
                'offset': offset,
                'limit': limit,
                'total': total,
            },
            'data': [
                {
                    'terms': ngram.terms,
                    'count': ngram.count,
                }
                for ngram in ngrams_query[offset : offset+limit]
            ],
        })

class NodesChildrenQueries(APIView):
    def _sql(self, input, node_id):
        session = get_session()
        fields = dict()
        tables = set('nodes')
        hyperdata_aliases = dict()
        # retrieve all unique fields names
        fields_names = input['retrieve']['fields'].copy()
        fields_names += [filter['field'] for filter in input['filters']]
        fields_names += input['sort']
        fields_names = set(fields_names)
        # relate fields to their respective ORM counterparts
        for field_name in fields_names:
            field_name_parts = field_name.split('.')
            field = None
            if len(field_name_parts) == 1:
                field = getattr(Node, field_name)
            elif field_name_parts[1] == 'count':
                if field_name_parts[0] == 'nodes':
                    field = func.count(Node.id)
                elif field_name_parts[0] == 'ngrams':
                    field = func.count(Ngram.id)
                    tables.add('ngrams')
            elif field_name_parts[0] == 'ngrams':
                field = getattr(Ngram, field_name_parts[1])
                tables.add('ngrams')
            elif field_name_parts[0] == 'hyperdata':
                hyperdata = _hyperdata_dict[field_name_parts[1]]
                if hyperdata not in hyperdata_aliases:
                    hyperdata_aliases[hyperdata] = aliased(Node_Hyperdata)
                hyperdata_alias = hyperdata_aliases[hyperdata]
                field = getattr(hyperdata_alias, 'value_%s' % hyperdata.type)
                if len(field_name_parts) == 3:
                    field = func.date_trunc(field_name_parts[2], field)
            fields[field_name] = field
        # build query: selected fields
        query = (session
            .query(*(fields[field_name] for field_name in input['retrieve']['fields']))
        )
        # build query: selected tables
        query = query.select_from(Node)
        if 'ngrams' in tables:
            query = (query
                .join(Node_Ngram, Node_Ngram.node_id == Node.id)
                .join(Ngram, Ngram.id == Node_Ngram.ngram_id)
            )
        for hyperdata, hyperdata_alias in hyperdata_aliases.items():
            query = (query
                .join(hyperdata_alias, hyperdata_alias.node_id == Node.id)
                .filter(hyperdata_alias.hyperdata_id == hyperdata.id)
            )
        # build query: filtering
        query = (query
            .filter(Node.parent_id == node_id)
        )
        for filter in input['filters']:
            query = (query
                .filter(_operators_dict[filter['operator']](
                    fields[filter['field']],
                    filter['value']
                ))
            )
        # build query: aggregations
        if input['retrieve']['aggregate']:
            for field_name in input['retrieve']['fields']:
                if not field_name.endswith('.count'):
                    query = query.group_by(fields[field_name])
        # build query: sorting
        for field_name in input['sort']:
            last = field_name[-1:]
            if last in ('+', '-'):
                field_name = field_name[:-1]
            if last == '-':
                query = query.order_by(fields[field_name].desc())
            else:
                query = query.order_by(fields[field_name])
        # build and return result
        output = copy.deepcopy(input)
        output['pagination']['total'] = query.count()
        output['results'] = list(
            query[input['pagination']['offset']:input['pagination']['offset']+input['pagination']['limit']]
            if input['pagination']['limit']
            else query[input['pagination']['offset']:]
        )
        return output
        session.remove()

    def _haskell(self, input, node_id):
        output = copy.deepcopy(input)
        output['pagination']['total'] = 0
        output['results'] = list()
        return output

    def post(self, request, node_id):
        """ Query the children of the given node.

            Example #1
            ----------

            Input:
            {
                "pagination": {
                    "offset": 0,
                    "limit": 10
                },
                "retrieve": {
                    "type": "fields",
                    "list": ["name", "hyperdata.publication_date"]
                },
                "filters": [
                    {"field": "hyperdata.publication_date", "operator": ">", "value": "2010-01-01 00:00:00"},
                    {"field": "ngrams.terms", "operator": "in", "value": ["bee", "bees"]}
                ],
                "sort": ["name"]
            }

            Output:
            {
                "pagination": {
                    "offset": 0,
                    "limit": 10
                },
                "retrieve": {
                    "type": "fields",
                    "list": ["name", "hyperdata.publication_date"]
                },
                "results": [
                    {"id": 12, "name": "A document about bees", "publication_date": "2014-12-03 10:00:00"},
                    ...,
                ]
            }
        """

        # authorized field names
        sql_fields = set({
            'id', 'name',
            'nodes.count',
            'nodes.countnorm',
            'ngrams.count',
            'ngrams.terms', 'ngrams.n',
        })
        for hyperdata in _hyperdata_list:
            sql_fields.add('hyperdata.' + hyperdata.name)
            if hyperdata.type == 'datetime':
                for part in ['year', 'month', 'day', 'hour', 'minute']:
                    sql_fields.add('hyperdata.' + hyperdata.name + '.' + part)

        # authorized field names: Haskell
        haskell_fields = set({
            'haskell.test',
        })

        # authorized field names: all of them
        authorized_fields = sql_fields | haskell_fields

        # input validation
        input = validate(request.DATA, {'type': dict, 'items': {
            'pagination': {'type': dict, 'items': {
                'limit': {'type': int, 'default': 0},
                'offset': {'type': int, 'default': 0},
            }, 'default': {'limit': 0, 'offset': 0}},
            'filters': {'type': list, 'items': {'type': dict, 'items': {
                'field': {'type': str, 'required': True, 'range': authorized_fields},
                'operator': {'type': str, 'required': True, 'range': list(_operators_dict.keys())},
                'value': {'required': True},
            }}, 'default': list()},
            'retrieve': {'type': dict, 'required': True, 'items': {
                'aggregate': {'type': bool, 'default': False},
                'fields': {'type': list, 'items': {'type': str, 'range': authorized_fields}, 'range': (1, )},
            }},
            'sort': {'type': list, 'items': {'type': str}, 'default': list()},
        }})

        # return result, depending on the queried fields
        if set(input['retrieve']['fields']) <= sql_fields:
            method = self._sql
        elif set(input['retrieve']['fields']) <= haskell_fields:
            method = self._haskell
        else:
            raise ValidationException('queried fields are mixing incompatible types of fields')
        return JsonHttpResponse(method(input, node_id), 201)

class NodesList(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)

    def get(self, request):
        session = get_session()
        
        print("user id : " + str(request.user))
        query = (session
            .query(Node.id, Node.name, NodeType.name.label('type'))
            .filter(Node.user_id == int(request.user.id))
            .join(NodeType)
        )
        if 'type' in request.GET:
            query = query.filter(NodeType.name == request.GET['type'])
        if 'parent' in request.GET:
            query = query.filter(Node.parent_id == int(request.GET['parent']))

        return JsonHttpResponse({'data': [
            node._asdict()
            for node in query.all()
        ]})
        
        session.remove()

class Nodes(APIView):
    def get(self, request, node_id):
        session = get_session()
        
        node = session.query(Node).filter(Node.id == node_id).first()
        if node is None:
            raise APIException('This node does not exist', 404)
        return JsonHttpResponse({
            'id': node.id,
            'name': node.name,
            'parent_id': node.parent_id,
            'type': cache.NodeType[node.type_id].name,
            # 'type': node.type__name,
            #'hyperdata': dict(node.hyperdata),
            'hyperdata': node.hyperdata,
        })
        
        session.remove()

    # deleting node by id
    # currently, very dangerous.
    # it should take the subnodes into account as well,
    # for better constistency...
    def delete(self, request, node_id):

        session = get_session()
        
        user = request.user
        node = session.query(Node).filter(Node.id == node_id).first()

        msgres = str()

        try:

            move_to_trash(node_id)
            msgres = node_id+" moved to Trash"

        except Exception as error:
            msgres ="error deleting : " + node_id + str(error)
        
        session.remove()

class CorpusController:
    @classmethod
    def get(cls, corpus_id):
        try:
            corpus_id = int(corpus_id)
        except:
            raise ValidationError('Corpora are identified by an integer.', 400)
        session = get_session()
        corpusQuery = session.query(Node).filter(Node.id == corpus_id).first()
        # print(str(corpusQuery))
        # raise Http404("404 error.")
        if not corpusQuery:
            raise Http404("No such corpus: %d" % (corpus_id, ))
        corpus = corpusQuery.first()
        if corpus.type.name != 'Corpus':
            raise Http404("No such corpus: %d" % (corpus_id, ))
        # if corpus.user != request.user:
        #     raise Http403("Unauthorized access.")
        return corpus
        session.remove()

    @classmethod
    def ngrams(cls, request, node_id):

        # parameters retrieval and validation
        startwith = request.GET.get('startwith', '').replace("'", "\\'")

        # build query
        ParentNode = aliased(Node)
        session = get_session()
        
        query = (session
            .query(Ngram.terms, func.count('*'))
            .join(Node_Ngram, Node_Ngram.ngram_id == Ngram.id)
            .join(Node, Node.id == Node_Ngram.node_id)
            .join(ParentNode, ParentNode.id == Node.parent_id)
            .filter(ParentNode.id == node_id)
            .filter(Ngram.terms.like('%s%%' % (startwith, )))
            .group_by(Ngram.terms)
            .order_by(func.count('*').desc())
        )

        # response building
        format = request.GET.get('format', 'json')
        if format == 'json':
            return JsonHttpResponse({
                "data": [{
                    'terms': row[0],
                    'occurrences': row[1]
                } for row in query.all()],
            })
        elif format == 'csv':
            return CsvHttpResponse(
                [['terms', 'occurences']] + [row for row in query.all()]
            )
        else:
            raise ValidationError('Unrecognized "format=%s", should be "csv" or "json"' % (format, ))

        session.remove()
