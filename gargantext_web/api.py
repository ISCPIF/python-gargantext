from django.http import HttpResponseNotFound, HttpResponse, Http404
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.core.exceptions import ValidationError

from django.db.models import Avg, Max, Min, Count
from node.models import NodeType, Node, Ngram

from django.db import connection

# from node.models import Language, ResourceType, Resource
# from node.models import Node, NodeType, Node_Resource, Project, Corpus
# from node.admin import CorpusForm, ProjectForm, ResourceForm

import json
def JsonHttpResponse(data, status=200):
    return HttpResponse(
        content      = json.dumps(data, indent=4),
        content_type = "application/json",
        status       = status
    )
Http400 = SuspiciousOperation
Http403 = PermissionDenied

_ngrams_order_columns = {
    "frequency" : "-count",
    "alphabetical" : "terms"
}


def corpus_ngrams(request, corpus_id):
    # parameters retrieval and control
    corpusQuery = Node.objects.filter(id = corpus_id)
    if not corpusQuery:
        raise Http404("No such corpus.")
    corpus = corpusQuery.first()
    if corpus.type.name != 'Corpus':
        raise Http404("No such corpus.")
    order = request.GET.get('order', 'frequency')
    if order not in _ngrams_order_columns:
        raise ValidationError('The order parameter should take one of the following values: ' +  ', '.join(_ngrams_order_columns), 400)
    order_column = _ngrams_order_columns[order]
    # query building
    ngramsQuery = Ngram.objects.filter(
        nodes__parent     = corpus,
        terms__startswith = request.GET.get('startswith', '')
    ).annotate(count=Count('id'))
    # how should we order this?
    orderColumn = {
        "frequency" : "-count",
        "alphabetical" : "terms"
    }.get(request.GET.get('order', 'frequency'), '-count')
    ngramsQuery = ngramsQuery.order_by(orderColumn)
    # response building
    return JsonHttpResponse({
        "list" : [ngram.terms for ngram in ngramsQuery],
    })

def corpus_metadata(request, corpus_id):
    # parameters retrieval and control
    corpusQuery = Node.objects.filter(id = corpus_id)
    if not corpusQuery:
        raise Http404("No such corpus.")
    corpus = corpusQuery.first()
    if corpus.type.name != 'Corpus':
        raise Http404("No such corpus.")
    # query building
    cursor = connection.cursor()
    cursor.execute(
    ''' SELECT
            key,
            COUNT(*) AS count
        FROM (
            SELECT skeys(metadata) AS key
            FROM %s
        ) AS keys
        GROUP BY 
            key
        ORDER BY
            count DESC
    ''' % (Node._meta.db_table, ))
    # response building
    return JsonHttpResponse({
        "list" : [row[0] for row in cursor.fetchall()],
    })