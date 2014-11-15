from django.http import HttpResponseNotFound, HttpResponse, HttpResponseBadRequest

from django.db.models import Avg, Max, Min, Count
from node.models import NodeType, Node, Ngram

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

_ngrams_order_columns = {
    "frequency" : "-count",
    "alphabetical" : "terms"
}

def ngrams(request, corpus_id):
    # parameters retrieval and control
    corpusQuery = Node.objects.filter(id = corpus_id)
    if not corpusQuery:
        return HttpResponseNotFound("No such corpus.")
    corpus = corpusQuery.first()
    if corpus.type.name != 'Corpus':
        return HttpResponseNotFound("No such corpus.")
    order = request.GET.get('order', 'frequency')
    if order not in _ngrams_order_columns:
        return HttpResponseBadRequest('The order parameter should take one of the following values: ' +  ', '.join(_ngrams_order_columns))
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