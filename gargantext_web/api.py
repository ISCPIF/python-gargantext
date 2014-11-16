from django.http import HttpResponseNotFound, HttpResponse, Http404
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.core.exceptions import ValidationError

from django.db.models import Avg, Max, Min, Count, Sum
from node.models import NodeType, Node, Node_Ngram, Ngram

from django.db import connection

# from node.models import Language, ResourceType, Resource
# from node.models import Node, NodeType, Node_Resource, Project, Corpus
# from node.admin import CorpusForm, ProjectForm, ResourceForm

def DebugHttpResponse(data):
    return HttpResponse('<html><body style="background:#000;color:#FFF"><pre>%s</pre></body></html>' % (str(data), ))

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

    @classmethod
    def get(cls, corpus_id):
        try:
            corpus_id = int(corpus_id)
        except:
            raise ValidationError('Corpora are identified by an integer.', 400)
        corpusQuery = Node.objects.filter(id = corpus_id)
        # print(str(corpusQuery))
        # raise Http404("C'est toujours ça de pris.")
        if not corpusQuery:
            raise Http404("No such corpus: %d" % (corpus_id, ))
        corpus = corpusQuery.first()
        if corpus.type.name != 'Corpus':
            raise Http404("No such corpus. %d" % (corpus_id, ))
        return corpus

    
    @classmethod
    def ngrams(cls, request, corpus_id):
        # parameters retrieval and validation
        corpus = cls.get(corpus_id)
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

    @classmethod
    def metadata(cls, request, corpus_id):
        # parameters retrieval and validation
        corpus = cls.get(corpus_id)
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
        
    @classmethod
    def data(cls, request, corpus_id):
        # parameters retrieval and validation
        corpus = cls.get(corpus_id)
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
                columns.append("%s.metadata->'%s' AS c%d" % (Node._meta.db_table, key, c, ))
                conditions.append("%s.metadata ? '%s'" % (Node._meta.db_table, key, ))
                group.append("c%d" % (c, ))
                order.append("c%d" % (c, ))
            else:
                raise ValidationError('Unrecognized type "%s" in "parameter[]=%s"' % (origin, parameter, ))
        # query building: mesured value
        mesured = request.GET.get('mesured', '')
        c = len(columns)
        if mesured == "documents.count":
            columns.append("COUNT(%s.id) AS c%d " % (Node._meta.db_table, c, ))
        elif mesured == "ngrams.count":
            columns.append("COUNT(%s.id) AS c%d " % (Ngram._meta.db_table, c, ))
            # return HttpResponse(query)
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
                    conditions.append("%s.terms IN ('%s')" % (Ngram._meta.db_table, "', '".join(values), ))
                    join_ngrams = True
            else:
                raise ValidationError('Unrecognized "filter[]=%s"' % (filter, ))
        # query building: initializing SQL
        sql = str(corpus.descendants().query)
        sql_array_select = sql.split('SELECT')
        sql_array_from = sql_array_select[-1].split('FROM')
        sql_array_where = sql_array_from[-1].split('WHERE')
        sql_array_order = sql_array_where[-1].split('ORDER')
        sql_0 = ''' WITH RECURSIVE cte (
            "depth", "path", "ordering", "id") AS (
                
            SELECT 1 AS depth,
            array[T."id"] AS path,
            array[T."id"] AS ordering,
            T."id"
            FROM  node_node T
            WHERE T."parent_id" IS NULL

            UNION ALL

            SELECT cte.depth + 1 AS depth,
            cte.path || T."id",
            cte.ordering || array[T."id"],
            T."id"
            FROM  node_node T
            JOIN  cte ON T."parent_id" = cte."id")
        '''
        sql_1 = '\nSELECT '
        sql_2 = '\nFROM %s\nINNER JOIN cte ON cte."id" = %s.id' % (Node._meta.db_table, Node._meta.db_table, )
        sql_3 = '\nWHERE ((NOT cte.id = \'%d\') AND (\'%d\' = ANY(cte."path")))' % (corpus.id, corpus.id, )
        # query building: assembling SQL
        sql_1 += ", ".join(columns)
        sql_2 += "\nINNER JOIN %s ON %s.id = %s.type_id" % (NodeType._meta.db_table, NodeType._meta.db_table, Node._meta.db_table, )
        if join_ngrams:
            sql_2 += "\nINNER JOIN %s ON %s.node_id = cte.id" % (Node_Ngram._meta.db_table, Node_Ngram._meta.db_table, )
            sql_2 += "\nINNER JOIN %s ON %s.id = %s.ngram_id" % (Ngram._meta.db_table, Ngram._meta.db_table, Node_Ngram._meta.db_table, )
        sql_3 += "\nAND %s.name = 'Document'" % (NodeType._meta.db_table, )
        if conditions:
            sql_3 += "\nAND (%s)" % (" AND ".join(conditions), )
        if group:
            sql_3 += "\nGROUP BY %s" % (", ".join(group), )
        if order:
            sql_3 += "\nORDER BY %s" % (", ".join(order), )
        sql = sql_0 + sql_1 + sql_2 + sql_3
        # query execution
        # return DebugHttpResponse(sql)
        cursor = connection.cursor()
        cursor.execute(sql)
        # response building
        return JsonHttpResponse({
            # "list": [{key:value for key, value in row.items() if isinstance(value, (str, int, float))} for row in query[:20].values()],
            "list": [row for row in cursor.fetchall()],
        })

