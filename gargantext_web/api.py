from django.http import HttpResponseNotFound, HttpResponse, Http404
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.core.exceptions import ValidationError

from django.db.models import Avg, Max, Min, Count
from node.models import NodeType, Node, Node_Ngram, Ngram

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


class CorpusController:

    @staticmethod
    def ngrams(request, corpus_id):
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

    @staticmethod
    def metadata(request, corpus_id):
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
        
    @staticmethod
    def data(request, corpus_id):
        # parameters retrieval and control
        corpusQuery = Node.objects.filter(id = corpus_id)
        if not corpusQuery:
            raise Http404("No such corpus.")
        corpus = corpusQuery.first()
        if corpus.type.name != 'Corpus':
            raise Http404("No such corpus.")
        # query building: initialization
        columns     = []
        conditions  = []
        group       = []
        order       = []
        join_ngrams = False
        # query building: parameters
        for parameter in request.GET.getlist('parameters[]'):
            c = len(columns)
            parameter_array = parameter.split('.')
            if len(parameter_array) != 2:
                raise ValidationError('Unrecognized "parameter[]=%s"' % (parameter, ))
            origin = parameter_array[0]
            key = parameter_array[1]
            if origin == "metadata":
                key = key.replace('\'', '\\\'')
                columns.append("node.metadata->'%s' AS c%d" % (key, c, ))
                conditions.append("node.metadata ? '%s'" % (key, ))
                group.append("c%d" % (c, ))
                order.append("c%d" % (c, ))
            else:
                raise ValidationError('Unrecognized type "%s" in "parameter[]=%s"' % (origin, parameter, ))
        # query building: mesured value
        mesured = request.GET.get('mesured', '')
        c = len(columns)
        if mesured == "documents.count":
            columns.append("COUNT(node.id) AS c%d " % (c, ))
        elif mesured == "ngrams.count":
            columns.append("COUNT(ngram.id) AS c%d " % (c, ))
            join_ngrams = True
        else:
            raise ValidationError('The "mesured" parameter should take one of the following values: "documents.count", "ngrams.count"')
        # query building: filters
        for filter in request.GET.getlist('filters[]', ''):
            if '|' in filter:
                filter_array = filter.split("|")
                key = filter_array[0]
                values = filter_array[1].replace("'", "\\'").split(",")
                if key == 'ngram.terms':
                    conditions.append("ngram.terms IN ('%s')" % ("', '".join(values), ))
                    join_ngrams = True
            else:
                raise ValidationError('Unrecognized "filter[]=%s"' % (filter, ))
        # query building: assembling
        sql = "SELECT %s FROM %s AS node" % (', '.join(columns), Node._meta.db_table, )
        if join_ngrams:
            sql += " INNER JOIN %s AS node_ngram ON node_ngram.node_id = node.id" % (Node_Ngram._meta.db_table, )
            sql += " INNER JOIN %s AS ngram ON ngram.id = node_ngram.ngram_id" % (Ngram._meta.db_table, )
        if conditions:
            sql += " WHERE %s" % (" AND ".join(conditions), )
        if group:
            sql += " GROUP BY %s" % (", ".join(group), )
        if order:
            sql += " ORDER BY %s" % (", ".join(order), )
        # query execution
        # return HttpResponse(sql)
        cursor = connection.cursor()
        cursor.execute(sql)
        # response building
        return JsonHttpResponse({
            "list": [row for row in cursor.fetchall()],
        })

