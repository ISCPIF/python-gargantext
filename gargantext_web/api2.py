from django.http import HttpResponse, Http404
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse

from sqlalchemy import text, distinct, or_,not_
from sqlalchemy.sql import func
from sqlalchemy.orm import aliased

import datetime
import copy
import collections

from gargantext_web.views import move_to_trash
from gargantext_web.db import *
from gargantext_web.views import session
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


from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import APIException as _APIException

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
        column_x = func.date_trunc(input['x']['resolution'], Node_Hyperdata.value_datetime)
        column_y = {
            'documents_count':  func.count(Node.id.distinct()),
            'ngrams_count':     func.sum(Node_Ngram.weight),
            # 'ngrams_tfidf':     func.sum(Node_Node_Ngram.weight),
        }[input['y']['value']]
        # build query: base
        query_base = (session
            .query(column_x)
            .select_from(Node)
            .join(Node_Ngram, Node_Ngram.node_id == Node.id)
            .join(Node_Hyperdata, Node_Hyperdata.node_id == Node_Ngram.node_id)
            .join(Hyperdata, Hyperdata.id == Node_Hyperdata.hyperdata_id)
            .filter(Hyperdata.name == input['x']['value'])
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
                query_base = query_base.filter(Node_Hyperdata.value_datetime >= input['filter']['date']['min'])
            if 'max' in input['filter']['date']:
                query_base = query_base.filter(Node_Hyperdata.value_datetime <= input['filter']['date']['max'])
        # build query: filter by ngrams
        query_result = query_base.add_columns(column_y)
        if 'ngrams' in input['filter'] and input['filter']['ngrams']:
            query_result = (query_result
                .join(Ngram, Ngram.id == Node_Ngram.ngram_id)
                .filter(Ngram.terms.in_(input['filter']['ngrams']))
            )
        # build query: filter by metadata
        if 'hyperdata' in input['filter']:
            for h, hyperdata in enumerate(input['filter']['hyperdata']):
                # get hyperdata in database
                hyperdata_model = (session
                    .query(Hyperdata.id, Hyperdata.type)
                    .filter(Hyperdata.name == hyperdata['key'])
                ).first()
                if hyperdata_model is None:
                    continue
                hyperdata_id, hyperdata_type = hyperdata_model
                # create alias and query it
                NH = aliased(Node_Hyperdata)
                NH_column = getattr(NH, 'value_' + hyperdata_type)
                operator = self._operators[hyperdata['operator']]
                value = self._converters[hyperdata_type](hyperdata['value'])
                query_result = (query_result
                    .join(NH, NH.node_id == Node.id)
                    .filter(NH.hyperdata_id == hyperdata_id)
                    .filter(operator(NH_column, value))
                )
        # build result: prepare data
        date_value_list = query_result.all()
        if date_value_list:
            date_min = date_value_list[0][0].replace(tzinfo=None)
            date_max = date_value_list[-1][0].replace(tzinfo=None)
        # build result: prepare interval
        result = collections.OrderedDict()
        if input['x']['with_empty'] and date_value_list:
            compute_next_date = self._resolutions[input['x']['resolution']]
            date = date_min
            while date <= date_max:
                result[date] = 0.0
                date = compute_next_date(date)
        # build result: integrate
        for date, value in date_value_list:
            result[date.replace(tzinfo=None)] = value
        # build result: normalize
        query_normalize = None
        if date_value_list and 'divided_by' in input['y'] and input['y']['divided_by']:
            if input['y']['divided_by'] == 'total_documents_count':
                query_normalize = query_base.add_column(func.count(Node.id.distinct()))
            elif input['y']['divided_by'] == 'total_ngrams_count':
                query_normalize = query_base.add_column(func.sum(Node_Ngram.weight))
        if query_normalize is not None:
            for date, value in query_normalize:
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

