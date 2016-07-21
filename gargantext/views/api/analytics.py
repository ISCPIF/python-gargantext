

from gargantext.util.http       import ValidationException, APIView \
                                     , get_parameters, JsonHttpResponse, Http404\
                                     , HttpResponse


from gargantext.util.db         import session, delete, func, bulk_insert

from gargantext.models          import Node, Ngram, NodeNgram, NodeNodeNgram, NodeNode, NodeHyperdata, HyperdataKey
from gargantext.constants       import INDEXED_HYPERDATA

from django.core.exceptions import PermissionDenied, SuspiciousOperation

from sqlalchemy import or_, not_
from sqlalchemy.sql import func
from sqlalchemy.orm import aliased

import datetime
import collections

from gargantext.util.db import *
from gargantext.util.validation import validate

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import APIException as _APIException


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


class APIException(_APIException):
    def __init__(self, message, code=500):
        self.status_code = code
        self.detail = message

class NodeNgramsQueries(APIView):

    _resolutions = {
        'second':   lambda d: d + datetime.timedelta(seconds=1),
        'minute':   lambda d: d + datetime.timedelta(minutes=1),
        'hour':     lambda d: d + datetime.timedelta(hours=1),
        'day':      lambda d: d + datetime.timedelta(days=1),
        'week':     lambda d: d + datetime.timedelta(days=7),
        'month':    lambda d: (d + datetime.timedelta(days=32)).replace(day=1),
        'year':     lambda d: (d + datetime.timedelta(days=367)).replace(day=1, month=1),
        'decade':   lambda d: (d + datetime.timedelta(days=3660)).replace(day=1, month=1),
        'century':  lambda d: (d + datetime.timedelta(days=36600)).replace(day=1, month=1),
    }

    _operators = {
        '=': lambda field, value: (field == value),
        '!=': lambda field, value: (field != value),
        '<': lambda field, value: (field < value),
        '>': lambda field, value: (field > value),
        '<=': lambda field, value: (field <= value),
        '>=': lambda field, value: (field >= value),
        'in': lambda field, value: (or_(*tuple(field == x for x in value))),
        'contains': lambda field, value: (field.contains(value)),
        'doesnotcontain': lambda field, value: (not_(field.contains(value))),
        'startswith': lambda field, value: (field.startswith(value)),
        'endswith': lambda field, value: (field.endswith(value)),
    }

    _converters = {
        'float': float,
        'int': int,
        'datetime': lambda x: x + '2000-01-01 00:00:00Z'[len(x):],
        'text': str,
        'string': str,
    }


    def post(self, request, project_id):

        # example only

        input = request.data or {
            'x': {
                'with_empty': True,
                'resolution': 'decade',
                'value': 'publication_date',
            },
            'y': {
                # 'divided_by': 'total_ngrams_count',
                # 'divided_by': 'total_documents_count',
            },
            'filter': {
                # 'ngrams': ['bees', 'bee', 'honeybee', 'honeybees', 'honey bee', 'honey bees'],
                # 'ngrams': ['insecticide', 'pesticide'],
                # 'corpora': [52633],
                # 'date': {'min': '1995-12-31'}
            },
            # 'format': 'csv',
        }
        print(input)
        # input validation
        input = validate(input, {'type': dict, 'default': {}, 'items': {
            'x': {'type': dict, 'default': {}, 'items': {
                # which hyperdata to choose for the date
                'value': {'type': str, 'default': 'publication_date', 'range': {'publication_date', }},
                # time resolution
                'resolution': {'type': str, 'range': self._resolutions.keys(), 'default': 'month'},
                # should we add zeroes for empty values?
                'with_empty': {'type': bool, 'default': False},
            }},
            'y': {'type': dict, 'default': {}, 'items': {
                # mesured value
                'value': {'type': str, 'default': 'ngrams_count', 'range': {'ngrams_count', 'documents_count', 'ngrams_tfidf'}},
                # value by which we should normalize
                'divided_by': {'type': str, 'range': {'total_documents_count', 'documents_count', 'total_ngrams_count'}},
            }},
            # filtering
            'filter': {'type': dict, 'default': {}, 'items': {
                # filter by metadata
                'hyperdata': {'type': list, 'default': [], 'items': {'type': dict, 'items': {
                    'key': {'type': str, 'range': self._operators.keys()},
                    'operator': {'type': str},
                    'value': {'type': str},
                }}},
                # filter by date
                'date': {'type': dict, 'items': {
                    'min': {'type': datetime.datetime},
                    'max': {'type': datetime.datetime},
                }, 'default': {}},
                # filter by corpora
                'corpora' : {'type': list, 'default': [], 'items': {'type': int}},
                # filter by ngrams
                'ngrams' : {'type': list, 'default': [], 'items': {'type': str}},
            }},
            # output format
            'format': {'type': str, 'default': 'json', 'range': {'json', 'csv'}},
        }})
        # build query: prepare columns
        X = aliased(NodeHyperdata)
        column_x = func.date_trunc(input['x']['resolution'], X.value_utc)
        column_y = {
            'documents_count':  func.count(Node.id.distinct()),
            'ngrams_count':     func.sum(NodeNgram.weight),
            # 'ngrams_tfidf':     func.sum(NodeNodeNgram.weight),
        }[input['y']['value']]
        # build query: base
        print(input)
        query_base = (session
            .query(column_x)
            .select_from(Node)
            .join(NodeNgram     , NodeNgram.node_id == Node.id)
            .join(X , X.node_id == NodeNgram.node_id)
            #.filter(X.key == input['x']['value'])
            .group_by(column_x)
            .order_by(column_x)
        )
        # build query: base, filter by corpora or project
        if 'corpora' in input['filter'] and input['filter']['corpora']:
            query_base = (query_base
                .filter(Node.parent_id.in_(input['filter']['corpora']))
            )
        else:
            ParentNode = aliased(Node)
            query_base = (query_base
                .join(ParentNode, ParentNode.id == Node.parent_id)
                .filter(ParentNode.parent_id == project_id)
            )
        # build query: base, filter by date
        if 'date' in input['filter']:
            if 'min' in input['filter']['date']:
                query_base = query_base.filter(X.value >= input['filter']['date']['min'])
            if 'max' in input['filter']['date']:
                query_base = query_base.filter(X.value <= input['filter']['date']['max'])
        # build query: filter by ngrams
        query_result = query_base.add_columns(column_y)
        if 'ngrams' in input['filter'] and input['filter']['ngrams']:
            query_result = (query_result
                .join(Ngram, Ngram.id == NodeNgram.ngram_id)
                .filter(Ngram.terms.in_(input['filter']['ngrams']))
            )
        # build query: filter by metadata
        if 'hyperdata' in input['filter']:
            for h, hyperdata in enumerate(input['filter']['hyperdata']):
                print(h,hyperdata)
                # get hyperdata in database
                #if hyperdata_model is None:
                #    continue
                #hyperdata_id, hyperdata_type = hyperdata_model
                # create alias and query it
                operator = self._operators[hyperdata['operator']]
                type_string = type2string(INDEXED_HYPERDATA[hyperdata['key']]['type'])
                value = self._converters[type_string](hyperdata['value'])
                query_result = (query_result
                    .join(NodeHyperdata , NodeHyperdata.node_id == NodeNgram.node_id)
                    .filter(NodeHyperdata.key == hyperdata['key'])
                    .filter(operator(NodeHyperdata.value, value))
                )
        # build result: prepare data
        date_value_list = query_result.all()
        #print(date_value_list)

        if date_value_list:
            date_min = date_value_list[0][0].replace(tzinfo=None)
            date_max = date_value_list[-2][0].replace(tzinfo=None)
        # build result: prepare interval
        result = collections.OrderedDict()
        if input['x']['with_empty'] and date_value_list:
            compute_next_date = self._resolutions[input['x']['resolution']]
            date = date_min
            while date <= date_max:
                result[date] = 0.0
                date = compute_next_date(date)
        # build result: integrate
        for date, value in date_value_list[0:-1]:
            result[date.replace(tzinfo=None)] = value
        # build result: normalize
        query_normalize = None
        if date_value_list and 'divided_by' in input['y'] and input['y']['divided_by']:
            if input['y']['divided_by'] == 'total_documents_count':
                query_normalize = query_base.add_column(func.count(Node.id.distinct()))
            elif input['y']['divided_by'] == 'total_ngrams_count':
                query_normalize = query_base.add_column(func.sum(NodeNgram.weight))
        if query_normalize is not None:
            for date, value in query_normalize[0:-1]:
                date = date.replace(tzinfo=None)
                if date in result:
                    result[date] /= value
        # return result with proper formatting
        if input['format'] == 'json':
            return JsonHttpResponse({
                'query': input,
                'result': sorted(result.items()),
            }, 201)
        elif input['format'] == 'csv':
            return CsvHttpResponse(sorted(result.items()), ('date', 'value'), 201)



# ?? TODO put in an ngrams.py file separately ?
# remark: 
#     the post() function is not used for analytics
#     but was added here to use the same url "api/ngrams"
class ApiNgrams(APIView):

    def get(self, request):

        # parameters retrieval and validation
        startwith = request.GET.get('startwith', '').replace("'", "\\'")

        # query ngrams
        ParentNode = aliased(Node)
        ngrams_query = (session
            .query(Ngram.id, Ngram.terms, func.sum(NodeNgram.weight).label('count'))
            .join(NodeNgram, NodeNgram.ngram_id == Ngram.id)
            .join(Node, Node.id == NodeNgram.node_id)
            .group_by(Ngram.id, Ngram.terms)
            # .group_by(Ngram)
            .order_by(func.sum(NodeNgram.weight).desc(), Ngram.terms)
        )

        # filters
        if 'startwith' in request.GET:
            ngrams_query = ngrams_query.filter(Ngram.terms.startswith(request.GET['startwith']))
        if 'contain' in request.GET:
            print("request.GET['contain']")
            print(request.GET['contain'])
            ngrams_query = ngrams_query.filter(Ngram.terms.contains(request.GET['contain']))
        if 'corpus_id' in request.GET:
            corpus_id_list = list(map(int, request.GET.get('corpus_id', '').split(',')))
            if corpus_id_list and corpus_id_list[0]:
                ngrams_query = ngrams_query.filter(Node.parent_id.in_(corpus_id_list))
        if 'ngram_id' in request.GET:
            ngram_id_list = list(map(int, request.GET.get('ngram_id', '').split(',')))
            if ngram_id_list and ngram_id_list[0]:
                ngrams_query = ngrams_query.filter(Ngram.id.in_(ngram_id_list))

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
                    'id': ngram.id,
                    'terms': ngram.terms,
                    'count': ngram.count,
                }
                for ngram in ngrams_query[offset : offset+limit]
            ],
        })


    def put(self, request):
        """
        Basic external access for *creating an ngram*
        ---------------------------------------------

         1 - checks user authentication before any changes

         2 - adds the ngram to Ngram table in DB

         3 - (if corpus param is present)
             adds the ngram doc counts to NodeNgram table in DB
             (aka "index the ngram" throught the docs of the corpus)

         4 - returns json with:
             'msg'   => a success msg 
             'text'  => the initial text content
             'term'  => the normalized text content
             'id'    => the new ngram_id
             'count' => the number of docs with the ngram in the corpus
                        (if corpus param is present)

        possible inline parameters
        --------------------------
        @param    text=<ngram_string>         [required]
        @param    corpus=<CORPUS_ID>          [optional]
        """

        from sqlalchemy     import insert
        from sqlalchemy.exc import IntegrityError
        from re             import findall
        
        from gargantext.util.db_cache  import cache

        # import will implement the same text cleaning procedures as toolchain
        from gargantext.util.toolchain.parsing           import normalize_chars
        from gargantext.util.toolchain.ngrams_extraction import normalize_forms

        # for indexing
        from gargantext.util.toolchain.ngrams_addition   import index_new_ngrams

        # 1 - check user authentication
        if not request.user.is_authenticated():
            res = HttpResponse("Unauthorized")
            res.status_code = 401
            return res

        # the params
        params = get_parameters(request)

        print("PARAMS", [(i,v) for (i,v) in params.items()])

        if 'text' in params:
            original_text = str(params.pop('text'))
            ngram_str = normalize_forms(normalize_chars(original_text))
        else:
            raise ValidationException('The route PUT /api/ngrams/ is used to create a new ngram\
                                        It requires a "text" parameter,\
                                        for instance /api/ngrams?text=hydrometallurgy')

        # if we have a 'corpus' param (to do the indexing)...
        do_indexation = False
        if 'corpus' in params:
            # we retrieve the corpus...
            corpus_id = int(params.pop('corpus'))
            corpus_node = cache.Node[corpus_id]
            # and the user must also have rights on the corpus
            if request.user.id == corpus_node.user_id:
                do_indexation = True
            else:
                res = HttpResponse("Unauthorized")
                res.status_code = 401
                return res

        # number of "words" in the ngram
        ngram_size = len(findall(r' +', ngram_str)) + 1

        # do the additions
        try:
            log_msg = ""
            ngram_id = None
            preexisting = session.query(Ngram).filter(Ngram.terms==ngram_str).first()
            if preexisting is not None:
                ngram_id = preexisting.id
                log_msg += "ngram already existed (id %i)\n" % ngram_id
            else:
                # 2 - insert into Ngrams
                new_ngram = Ngram(terms=ngram_str, n=ngram_size)
                session.add(new_ngram)
                session.commit()
                ngram_id = new_ngram.id
                log_msg += "ngram was added with new id %i\n" % ngram_id

            # 3 - index the term
            if do_indexation:
                n_added = index_new_ngrams([ngram_id], corpus_node)
                log_msg += 'ngram indexed in corpus %i\n' % corpus_id

            return JsonHttpResponse({
                'msg': log_msg,
                'text': original_text,
                'term': ngram_str,
                'id' : ngram_id,
                'count': n_added if do_indexation else 'no corpus provided for indexation'
                }, 200)

        # just in case
        except Exception as e:
            return JsonHttpResponse({
                'msg': str(e),
                'text': original_text
                }, 400)


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

od = collections.OrderedDict(sorted(INDEXED_HYPERDATA.items()))

_hyperdata_list = [ { key : value }
            for key, value in od.items()
            if key != 'abstract'
         ]


def type2string(given_type):
    if given_type == int:
        return "integer"
    elif given_type == str:
        return "string"
    elif given_type == datetime.datetime:
        return "datetime"

def get_metadata(corpus_id_list):
    # query hyperdata keys
    ParentNode = aliased(Node)
    hyperdata_query = (session
        .query(NodeHyperdata.key)
        .join(Node, Node.id == NodeHyperdata.node_id)
        .filter(Node.parent_id.in_(corpus_id_list))
        .group_by(NodeHyperdata.key)
    )

    # build a collection with the hyperdata keys
    collection = []
    for hyperdata in INDEXED_HYPERDATA.keys():
        valuesCount = 0
        values = None

        # count values and determine their span
        values_count = None
        values_from  = None
        values_to    = None
#        if hyperdata == 'text':
#            node_hyperdata_query = (session
#                .query(NodeHyperdata.key)
#                .join(Node, Node.id == NodeHyperdata.node_id)
#                .filter(Node.parent_id.in_(corpus_id_list))
#                .filter(NodeHyperdata.key == hyperdata)
#                .group_by(NodeHyperdata.key)
#                .order_by(NodeHyperdata.key)
#            )
#            values_count = node_hyperdata_query.count()
#            # values_count, values_from, values_to = node_hyperdata_query.first()

        # if there is less than 32 values, retrieve them
        values = None
        if isinstance(values_count, int) and values_count <= 48:
            if hyperdata == 'datetime':
                values = [row.isoformat() for row in node_hyperdata_query.all()]
            else:
                values = [row for row in node_hyperdata_query.all()]

        # adding this hyperdata to the collection
        collection.append({
            'key': str(hyperdata),
            'type': type2string(INDEXED_HYPERDATA[hyperdata]['type']),
            'values': values,
            'valuesFrom': values_from,
            'valuesTo': values_to,
            'valuesCount': values_count,
        })

    # give the result back
    return collection

class ApiHyperdata(APIView):

    def get(self, request):
        corpus_id_list = list(map(int, request.GET['corpus_id'].split(',')))
        return JsonHttpResponse({
            'data': get_metadata(corpus_id_list),
        })
