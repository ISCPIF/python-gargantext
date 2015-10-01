from django.http import HttpResponse, Http404
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

from sqlalchemy import text, distinct, or_,not_
from sqlalchemy.sql import func, desc
from sqlalchemy.orm import aliased

import datetime
import copy

from gargantext_web.views import move_to_trash
from gargantext_web.db import session, Node, NodeNgram, NodeNgramNgram, NodeNodeNgram, Ngram, Hyperdata, Node_Ngram
from gargantext_web.db import get_or_create_node

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


from rest_framework.decorators import api_view
#@login_required
# TODO how to secure REST ?
class Ngrams(APIView):
    '''
    REST application to manage ngrams

    '''
    def get(self, request, node_id):
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

        order_query = request.GET.get('order', False)
        if order_query == 'cvalue':
            ngrams_query = ngrams_query.order_by(desc(Cvalue.score))
        elif order_query == 'tfidf':
            ngrams_query = ngrams_query.order_by(desc(Tfidf.score))
        elif order_query  == 'specificity':
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
        list_id = request.GET.get('list_id', False)
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
        elif list_id != False:
            list_id = int(list_id)
            node = session.query(Node).filter(Node.id==node_id).first()
            if node.type_id == cache.NodeType['StopList'].id or node.type_id == cache.NodeType['MiamList'].id:
                List = aliased(NodeNgram)
                ngrams_query = (ngrams_query.join(List, List.ngram_id == Ngram.id )
                                            .filter(List.node_id == node.id)
                                )
            elif node.type_id == cache.NodeType['Cooccurrence'].id:
                CoocX = aliased(NodeNgramNgram)
                CoocY = aliased(NodeNgramNgram)
                ngrams_query = (ngrams_query.join(CoocX, CoocX.ngramx_id == Ngram.id )
                                            .join(CoocY, CoocY.ngramy_id == Ngram.id)
                                            .filter(CoocX.node_id == node.id)
                                            .filter(CoocY.node_id == node.id)
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
#                         results = ['id', 'terms']
#                        { x : eval('ngram.' + x) for x in results
#                        } for ngram in ngrams_query[offset : offset+limit]

                    ],
                               })

