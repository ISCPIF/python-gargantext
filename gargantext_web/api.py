from django.http import HttpResponseNotFound, HttpResponse, Http404
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.core.exceptions import ValidationError

from django.db.models import Avg, Max, Min, Count, Sum
from node.models import NodeType, Node, Node_Ngram, Ngram

from django.db import connection

# from node.models import Language, ResourceType, Resource
# from node.models import Node, NodeType, Node_Resource, Project, Corpus
# from node.admin import CorpusForm, ProjectForm, ResourceForm

_sql_cte = '''
    WITH RECURSIVE cte ("depth", "path", "ordering", "id") AS (        
        SELECT 1 AS depth,
        array[T."id"] AS path,
        array[T."id"] AS ordering,
        T."id"
        FROM  %s T
        WHERE T."parent_id" IS NULL

        UNION ALL

        SELECT cte.depth + 1 AS depth,
        cte.path || T."id",
        cte.ordering || array[T."id"],
        T."id"
        FROM  %s T
        JOIN  cte ON T."parent_id" = cte."id"
    )
''' % (Node._meta.db_table, Node._meta.db_table, )

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

Http400 = SuspiciousOperation
Http403 = PermissionDenied

_ngrams_order_columns = {
    "frequency" : "-count",
    "alphabetical" : "terms"
}


class NodesController:

    @classmethod
    def get(cls, request):
        query = Node.objects
        if 'type' in request.GET:
            query = query.filter(type__name=request.GET['type'])
        if 'parent' in request.GET:
            query = query.filter(parent_id=int(request.GET['parent']))

        collection = []
        for child in query.all():
            type_name = child.type.name
            collection.append({
                'id': child.id,
                'text': child.name,
                'type': type_name,
                'children': type_name is not 'Document',
            })
        return JsonHttpResponse(collection)



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
            raise Http404("No such corpus: %d" % (corpus_id, ))
        # if corpus.user != request.user:
        #     raise Http403("Unauthorized access.")
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
        cursor = connection.cursor()
        cursor.execute(_sql_cte + '''
            SELECT ngram.terms, COUNT(*) AS occurrences
            FROM cte
            INNER JOIN %s AS node ON node.id = cte.id
            INNER JOIN %s AS nodetype ON nodetype.id = node.type_id
            INNER JOIN %s AS node_ngram ON node_ngram.node_id = node.id
            INNER JOIN %s AS ngram ON ngram.id = node_ngram.ngram_id
            WHERE (NOT cte.id = \'%d\') AND (\'%d\' = ANY(cte."path"))
            AND nodetype.name = 'Document'
            AND ngram.terms LIKE '%s%%'
            GROUP BY ngram.terms
            ORDER BY occurrences DESC
        ''' % (
            Node._meta.db_table,
            NodeType._meta.db_table,
            Node_Ngram._meta.db_table,
            Ngram._meta.db_table,
            corpus.id,
            corpus.id,
            request.GET.get('startwith', '').replace("'", "\\'"),
        ))
        # # response building
        # return JsonHttpResponse({
        #     "list" : [row[0] for row in cursor.fetchall()],
        # })

        # response building
        format = request.GET.get('format', 'json')
        if format == 'json':
            return JsonHttpResponse({
                "list": [{
                    'terms': row[0],
                    'occurrences': row[1]
                } for row in cursor.fetchall()],
            })
        elif format == 'csv':
            return CsvHttpResponse(
                [['terms', 'occurences']] + [row for row in cursor.fetchall()]
            )
        else:
            raise ValidationError('Unrecognized "format=%s", should be "csv" or "json"' % (format, ))

    @classmethod
    def metadata(cls, request, corpus_id):
        # parameters retrieval and validation
        corpus = cls.get(corpus_id)
        # query building
        cursor = connection.cursor()
        # cursor.execute(_sql_cte + '''
        #     SELECT key
        #     FROM (
        #         SELECT skeys(metadata) AS key, COUNT(*)
        #         FROM cte
        #         INNER JOIN %s AS node ON node.id = cte.id
        #         WHERE (NOT cte.id = \'%d\') AND (\'%d\' = ANY(cte."path"))
        #     ) AS keys
        #     GROUP BY key
        #     ORDER BY COUNT(*) DESC
        # ''' % (Node._meta.db_table, corpus.id, corpus.id, ))
        cursor.execute('''
            SELECT key, COUNT(*) AS count, (
                SELECT COUNT(DISTINCT metadata->key) FROM %s
            ) AS values
            FROM (
                SELECT skeys(metadata) AS key
                FROM %s
                WHERE parent_id = \'%d\'
            ) AS keys
            GROUP BY key
            ORDER BY count
        ''' % (Node._meta.db_table, Node._meta.db_table, corpus.id, ))
        # response building
        collection = []
        for row in cursor.fetchall():
            type = 'string'
            key = row[0]
            split_key = key.split('_')
            name = split_key[0]
            if len(split_key) == 2:
                if split_key[1] == 'date':
                    name = split_key[0]
                    type = 'datetime'
                elif row[0] == 'language_fullname':
                    name = 'language'
                    type = 'string'
                else:
                    continue
            values = None
            if row[2] < 32:
                cursor.execute('''
                    SELECT DISTINCT metadata->'%s'
                    FROM %s
                    WHERE parent_id = %s
                    AND metadata ? '%s'
                    ORDER BY metadata->'%s'
                ''' % (key, Node._meta.db_table, corpus.id, key, key, ))
                values = [row[0] for row in cursor.fetchall()]
            collection.append({
                'key': key,
                'text': name,
                'documents': row[1],
                'valuesCount': row[2],
                'values': values,
                'type': type,
            })
        return JsonHttpResponse(collection)
        
    @classmethod
    def data(cls, request, corpus_id):
        # parameters retrieval and validation
        corpus = cls.get(corpus_id)
        # query building: initialization
        columns     = []
        conditions  = []
        group       = []
        order       = []
        having      = []
        join_ngrams = False
        # query building: parameters
        parameters = request.GET.getlist('parameters[]')
        for parameter in parameters:
            c = len(columns)
            parameter_array = parameter.split('.')
            if len(parameter_array) != 2:
                raise ValidationError('Unrecognized "parameter[]=%s"' % (parameter, ))
            origin = parameter_array[0]
            key = parameter_array[1]
            if origin == "metadata":
                columns.append("%s.metadata->'%s' AS c%d" % (Node._meta.db_table, key, c, ))
                conditions.append("%s.metadata ? '%s'" % (Node._meta.db_table, key, ))
                # conditions.append("c%d IS NOT NULL" % (c, ))
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
            join_ngrams = True
        else:
            raise ValidationError('The "mesured" parameter should take one of the following values: "documents.count", "ngrams.count"')
        # query building: filters
        for filter in request.GET.getlist('filters[]', ''):
            splitFilter = filter.split('.')
            origin = splitFilter[0]
            # 127.0.0.1:8000/api/corpus/13410/data
            #     ?mesured=ngrams.count
            #     &parameters[]=metadata.publication_date
            #     &format=json
            #     &filters[]=ngrams.in.bee,bees
            #     &filters[]=metadata.language_fullname.eq.English
            #     &filters[]=metadata.publication_date.gt.1950-01-01
            #     &filters[]=metadata.publication_date.lt.2000-01-01
            #     &filters[]=metadata.title.contains.e
            if origin == 'ngrams':
                if splitFilter[1] == 'in':
                    ngrams = '.'.join(splitFilter[2:]).split(',')
                    map(str.strip, ngrams)
                    map(lambda ngram: ngram.replace("'", "''"), ngrams)
                    conditions.append(
                        "%s.terms IN ('%s')" % (Ngram._meta.db_table, "', '".join(ngrams), )
                    )
                    join_ngrams = True
            elif origin == 'metadata':
                key = splitFilter[1].replace("'", "''")
                operator = splitFilter[2]
                value = '.'.join(splitFilter[3:]).replace("'", "''")
                condition = "%s.metadata->'%s' " % (Node._meta.db_table, key, )
                if operator == 'contains':
                    condition += "LIKE '%%%s%%'" % (value, )
                else:
                    condition += {
                        'eq': '=',
                        'lt': '<=',
                        'gt': '>=',
                    }[operator]
                    condition += " '%s'" % (value, )
                conditions.append(condition)
            else:
                raise ValidationError('Unrecognized "filter[]=%s"' % (filter, ))
        # query building: initializing SQL
        sql_0 = ''
        sql_1 = '\nSELECT '
        sql_2 = '\nFROM %s' % (Node._meta.db_table, )
        sql_3 = '\nWHERE (%s.parent_id = %d)' % (Node._meta.db_table, corpus.id, )
        # sql_0 = _sql_cte
        # sql_1 = '\nSELECT '
        # sql_2 = '\nFROM %s\nINNER JOIN cte ON cte."id" = %s.id' % (Node._meta.db_table, Node._meta.db_table, )
        # sql_3 = '\nWHERE ((NOT cte.id = \'%d\') AND (\'%d\' = ANY(cte."path")))' % (corpus.id, corpus.id, )
        # query building: assembling SQL
        sql_1 += ", ".join(columns)
        sql_2 += "\nINNER JOIN %s ON %s.id = %s.type_id" % (NodeType._meta.db_table, NodeType._meta.db_table, Node._meta.db_table, )
        if join_ngrams:
            sql_2 += "\nINNER JOIN %s ON %s.node_id = %s.id" % (Node_Ngram._meta.db_table, Node_Ngram._meta.db_table, Node._meta.db_table, )
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
        format = request.GET.get('format', 'json')
        keys = parameters + [mesured]
        rows = cursor.fetchall()
        if format == 'json':
            dimensions = []
            for key in keys:
                suffix = key.split('_')[-1]
                dimensions.append({
                    'key': key,
                    'type': 'datetime' if suffix == 'date' else 'numeric'
                })
            return JsonHttpResponse({
                "collection": [
                    {key: value for key, value in zip(keys, row)}
                    for row in rows
                ],
                "list": [row for row in rows],
                "dimensions" : dimensions
            })
        elif format == 'csv':
            return CsvHttpResponse([keys] + [row for row in rows])
        else:
            raise ValidationError('Unrecognized "format=%s", should be "csv" or "json"' % (format, ))

