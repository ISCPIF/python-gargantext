from django.http import HttpResponseNotFound, HttpResponse, Http404
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.core.exceptions import ValidationError

from django.db.models import Avg, Max, Min, Count, Sum
# from node.models import Language, ResourceType, Resource
# from node.models import Node, NodeType, Node_Resource, Project, Corpus

from sqlalchemy import text
from sqlalchemy.sql import func
from sqlalchemy.orm import aliased

import node.models
NodeType = node.models.NodeType.sa
Node = node.models.Node.sa
Node_Ngram = node.models.Node_Ngram.sa
Ngram = node.models.Ngram.sa
Metadata = node.models.Metadata.sa
Node_Metadata = node.models.Node_Metadata.sa

def literalquery(statement, dialect=None):
    """Generate an SQL expression string with bound parameters rendered inline
    for the given SQLAlchemy statement.

    WARNING: This method of escaping is insecure, incomplete, and for debugging
    purposes only. Executing SQL statements with inline-rendered user values is
    extremely insecure.
    """
    from datetime import datetime
    import sqlalchemy.orm
    if isinstance(statement, sqlalchemy.orm.Query):
        if dialect is None:
            dialect = statement.session.get_bind(
                statement._mapper_zero_or_none()
            ).dialect
        statement = statement.statement
    if dialect is None:
        dialect = getattr(statement.bind, 'dialect', None)
    if dialect is None:
        from sqlalchemy.dialects import mysql
        dialect = mysql.dialect()

    Compiler = type(statement._compiler(dialect))

    class LiteralCompiler(Compiler):
        visit_bindparam = Compiler.render_literal_bindparam

        def render_literal_value(self, value, type_):
            return str(value)
            # if isinstance(value, (float, int)):
            #     return str(value)
            # elif isinstance(value, datetime):
            #     return repr(str(value))
            # else:  # fallback
            #     value = super(LiteralCompiler, self).render_literal_value(
            #         value, type_,
            #     )
            #     if isinstance(value, unicode):
            #         return value.encode('UTF-8')
            #     else:
            #         return value

    return LiteralCompiler(dialect, statement)

def get_connection():
    import sqlalchemy.orm
    from django.db import connections
    from aldjemy.core import get_engine
    alias = 'default'
    connection = connections[alias]
    session = sqlalchemy.orm.create_session()
    engine = get_engine()
    return engine.connect()


# connection = engine.connect()

# _sql_cte = '''
#     WITH RECURSIVE cte ("depth", "path", "ordering", "id") AS (        
#         SELECT 1 AS depth,
#         array[T."id"] AS path,
#         array[T."id"] AS ordering,
#         T."id"
#         FROM  %s T
#         WHERE T."parent_id" IS NULL

#         UNION ALL

#         SELECT cte.depth + 1 AS depth,
#         cte.path || T."id",
#         cte.ordering || array[T."id"],
#         T."id"
#         FROM  %s T
#         JOIN  cte ON T."parent_id" = cte."id"
#     )
# ''' % (Node._meta.db_table, Node._meta.db_table, )


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
    def ngrams(cls, request, node_id):

        # parameters retrieval and validation
        startwith = request.GET.get('startwith', '').replace("'", "\\'")

        # build query
        ParentNode = aliased(Node)
        query = (Ngram
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
                "collection": [{
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

    @classmethod
    def metadata(cls, request, node_id):
        
        # query metadata keys
        ParentNode = aliased(Node)
        metadata_query = (Metadata
            .query(Metadata)
            .join(Node_Metadata, Node_Metadata.metadata_id == Metadata.id)
            .join(Node, Node.id == Node_Metadata.node_id)
            .filter(Node.parent_id == node_id)
            .group_by(Metadata)
        )

        # build a collection with the metadata ekys
        collection = []
        for metadata in metadata_query:
            # count values
            value_column = getattr(Node_Metadata, 'value_' + metadata.type)
            node_metadata_query = (Node_Metadata
                .query(value_column)
                .join(Node, Node.id == Node_Metadata.node_id)
                .filter(Node.parent_id == node_id)
                .filter(Node_Metadata.metadata_id == metadata.id)
                .group_by(value_column)
                .order_by(value_column)
            )
            valuesCount = node_metadata_query.count()
            # if there is less than 32 values, retrieve them
            values = None
            if valuesCount <= 32:
                values = [row[0] for row in node_metadata_query.all()]
                if metadata.type == 'datetime':
                    values = []
                    values = map(lambda x: x.isoformat(), values)

            collection.append({
                'key': metadata.name,
                'values': values,
                'valuesCount': valuesCount,
            })

        return JsonHttpResponse({
            'test' : 123,
            'collection': collection,
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

