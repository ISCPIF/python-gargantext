from django.http import HttpResponseNotFound, HttpResponse, Http404
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.core.exceptions import ValidationError

from django.db.models import Avg, Max, Min, Count, Sum
# from node.models import Language, ResourceType, Resource
# from node.models import Node, NodeType, Node_Resource, Project, Corpus

from sqlalchemy import text, distinct
from sqlalchemy.sql import func
from sqlalchemy.orm import aliased

import node.models
NodeType = node.models.NodeType.sa
Node = node.models.Node.sa
Node_Ngram = node.models.Node_Ngram.sa
Ngram = node.models.Ngram.sa
Metadata = node.models.Metadata.sa
Node_Metadata = node.models.Node_Metadata.sa

# for debugging only
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
            return "'" + str(value) + "'"
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

# these might be used for SQLAlchemy
def get_session():
    import sqlalchemy.orm
    from django.db import connections
    from sqlalchemy.orm import sessionmaker
    from aldjemy.core import get_engine
    alias = 'default'
    connection = connections[alias]
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def get_connection():
    from aldjemy.core import get_engine
    engine = get_engine()
    return engine.connect()

# for recursive queries
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


# class HttpError(Exception):
    
#     def __init__(self, message, code):
#         self.message = message
#         self.code = code


# class RestHttpResponse(HttpResponse):

#     def __init__(self, request, *args, **kwargs):
#         message = None
#         method = None
#         try:
#             method = getattr(self, request.method.lower())
#         except:
#             status = 405
#             message = 'Method not allowed.'
#             return

#         # get input data
#         data = {}
#         data.update(request.GET)
#         data.update(request.POST)

#         # get the generated response
#         headers = {}
#         if method:
#             try:
#                 result = method(self, request, *args, **kwargs)
#                 if isinstance(result, tuple):
#                     data = result[0]
#                     status = result[1]
#                     if len(result) > 2:
#                         headers = result[2]
#                 else:
#                     data = result
#                     status = 200
#             except HttpError as e:
#                 message = e.message
#                 status = e.code

#         # generate the HTTP response
#         HttpResponse.__init__(self,
#             status=status,
#         )
#         for key, value in headers.items():
#             self[key] = value


#     def options(self, request, *args, **kwargs):
#         # methods = [name for name in list(vars(cls)) if callable(getattr(cls, name))]
#         # return '', 200, {'Allow': ','.join([
#         #     method.upper()
#         #     for method in methods
#         #     if method[0] != '_' and (method not in dir(RestHttpResponse) or method == 'options') and callable(RestHttpResponse, method)
#         # ])}
#         return '', 200, {'Allow': ','.join([method.upper() for method in dir(self) if method[0] != '_' and method in ['get', 'post', 'put', 'delete', 'options']])}


# delattr(RestHttpResponse, 'get')


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import APIException

_APIException = APIException
class APIException(_APIException):
    def __init__(self, message, code=500):
        self.status_code = code
        self.detail = message



_operators = {
    "=":            lambda field, value: (field == value),
    "!=":           lambda field, value: (field != value),
    "<":            lambda field, value: (field < value),
    ">":            lambda field, value: (field > value),
    "<=":           lambda field, value: (field <= value),
    ">=":           lambda field, value: (field >= value),
    "in":           lambda field, value: (field.in_(value)),
    "contains":     lambda field, value: (field.contains(value)),
    "startswith":   lambda field, value: (field.startswith(value)),
}

from rest_framework.decorators import api_view
@api_view(('GET',))
def Root(request, format=None):
    return Response({
        'users': reverse('user-list', request=request, format=format),
        'snippets': reverse('snippet-list', request=request, format=format)
    })


class NodesChildrenMetatadata(APIView):

    def get(self, request, node_id):
        
        # query metadata keys
        ParentNode = aliased(Node)
        metadata_query = (Metadata
            .query(Metadata)
            .join(Node_Metadata, Node_Metadata.metadata_id == Metadata.id)
            .join(Node, Node.id == Node_Metadata.node_id)
            .filter(Node.parent_id == node_id)
            .group_by(Metadata)
        )

        # build a collection with the metadata keys
        collection = []
        for metadata in metadata_query:
            valuesCount = 0
            values = None

            # count values and determine their span
            values_count = None
            values_from = None
            values_to = None
            if metadata.type != 'text':
                value_column = getattr(Node_Metadata, 'value_' + metadata.type)
                node_metadata_query = (Node_Metadata
                    .query(value_column)
                    .join(Node, Node.id == Node_Metadata.node_id)
                    .filter(Node.parent_id == node_id)
                    .filter(Node_Metadata.metadata_id == metadata.id)
                    .group_by(value_column)
                    .order_by(value_column)
                )
                values_count = node_metadata_query.count()
                # values_count, values_from, values_to = node_metadata_query.first()

            # if there is less than 32 values, retrieve them
            values = None
            if isinstance(values_count, int) and values_count <= 48:
                values = [row[0] for row in node_metadata_query.all()]
                if metadata.type == 'datetime':
                    values = []
                    values = map(lambda x: x.isoformat(), values)

            # adding this metadata to the collection
            collection.append({
                'key': metadata.name,
                'type': metadata.type,
                'values': values,
                'valuesFrom': values_from,
                'valuesTo': values_to,
                'valuesCount': values_count,
            })

        return JsonHttpResponse({
            'collection': collection,
        })



class NodesChildrenQueries(APIView):

    def _parse_filter(self, filter):
            
        # validate filter keys
        filter_keys = {'field', 'operator', 'value'}
        if set(filter) != filter_keys:
            raise APIException('Every filter should have exactly %d keys: "%s"'% (len(filter_keys), '", "'.join(filter_keys)), 400)
        field, operator, value = filter['field'], filter['operator'], filter['value']

        # validate operator
        if operator not in _operators:
            raise APIException('Invalid operator: "%s"'% (operator, ), 400)

        # validate value, depending on the operator
        if operator == 'in':
            if not isinstance(value, list):
                raise APIException('Parameter "value" should be an array when using operator "%s"'% (operator, ), 400)
            for v in value:
                if not isinstance(v, (int, float, str)):
                    raise APIException('Parameter "value" should be an array of numbers or strings when using operator "%s"'% (operator, ), 400)
        else:
            if not isinstance(value, (int, float, str)):
                raise APIException('Parameter "value" should be a number or string when using operator "%s"'% (operator, ), 400)

        # parse field
        field_objects = {
            'metadata': None,
            'ngrams': ['terms', 'n'],
        }
        field = field.split('.')
        if len(field) < 2 or field[0] not in field_objects:
            raise APIException('Parameter "field" should be a in the form "object.key", where "object" takes one of the following values: "%s". "%s" was found instead' % ('", "'.join(field_objects), '.'.join(field)), 400)
        if field_objects[field[0]] is not None and field[1] not in field_objects[field[0]]:
            raise APIException('Invalid key for "%s" in parameter "field", should be one of the following values: "%s". "%s" was found instead' % (field[0], '", "'.join(field_objects[field[0]]), field[1]), 400)

        # return value
        return field, _operators[operator], value


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
                    "list": ["name", "metadata.publication_date"]
                },
                "filters": [
                    {"field": "metadata.publication_date", "operator": ">", "value": "2010-01-01 00:00:00"},
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
                    "list": ["name", "metadata.publication_date"]
                },
                "results": [
                    {"id": 12, "name": "A document about bees", "publication_date": "2014-12-03 10:00:00"},
                    ...,
                ]
            }
        """

        # validate query
        query_fields = {'pagination', 'retrieve', 'sort', 'filters'}
        for key in request.DATA:
            if key not in query_fields:
                raise APIException('Unrecognized field "%s" in query object. Accepted fields are: "%s"' % (key, '", "'.join(query_fields)), 400)

        # selecting info
        if 'retrieve' not in request.DATA:
            raise APIException('The query should have a "retrieve" parameter.', 400)
        retrieve = request.DATA['retrieve']
        retrieve_types = {'fields', 'aggregates'}
        if 'type' not in retrieve:
            raise APIException('In the query\'s "retrieve" parameter, a "type" should be specified. Possible values are: "%s".' % ('", "'.join(retrieve_types), ), 400)
        if 'list' not in retrieve or not isinstance(retrieve['list'], list):
            raise APIException('In the query\'s "retrieve" parameter, a "list" should be provided as an array', 400)
        if retrieve['type'] not in retrieve_types:
            raise APIException('Unrecognized "type": "%s" in the query\'s "retrieve" parameter. Possible values are: "%s".' % (retrieve["type"], '", "'.join(retrieve_types), ), 400)
        fields_names = ['id'] + list(set(retrieve['list']) - {'id'})
        fields_list = []
        if retrieve['type'] == 'fields':
            for field_name in fields_names:
                split_field_name = field_name.split('.')
                if split_field_name[0] == 'metadata':
                    field = Node.metadata[split_field_name[1]]
                else:
                    authorized_field_names = {'id', 'name', }
                    if field_name not in authorized_field_names:
                        raise APIException('Unrecognized "field": "%s" in the query\'s "retrieve" parameter. Possible values are: "%s".' % (field_name, '", "'.join(authorized_field_names), ))
                    field = getattr(Node, field_name)
                fields_list.append(field.label(field_name))

        # starting the query!
        document_type_id = NodeType.query(NodeType.id).filter(NodeType.name == 'Document').scalar()
        query = (Node
            .query(*fields_list)
            .filter(Node.type_id == document_type_id)
            .filter(Node.parent_id == node_id)
        )

        # filtering
        metadata_aliases = {}
        for filter in request.DATA.get('filters', []):
            # parameters extraction & validation
            field, operator, value = self._parse_filter(filter)
            # 
            if field[0] == 'metadata':
                # which metadata?
                metadata = Metadata.query(Metadata).filter(Metadata.name == field[1]).first()
                if metadata is None:
                    metadata_query = Metadata.query(Metadata.name).order_by(Metadata.name)
                    metadata_names = [metadata.name for metadata in metadata_query.all()]
                    raise APIException('Invalid key for "%s" in parameter "field", should be one of the following values: "%s". "%s" was found instead' % (field[0], '", "'.join(metadata_names), field[1]), 400)                
                # check or create metadata tables; join if necessary
                ParentNode = aliased(Node)
                if field[1] not in metadata_aliases:
                    metadata_alias = metadata_aliases[field[1]] = aliased(Node_Metadata)
                    query = (query
                        .join(metadata_alias, metadata_alias.node_id == Node.id)
                        .filter(metadata_alias.metadata_id == metadata.id)
                    )
                else:
                    metadata_alias = metadata_aliases[field[1]]
                # filter query
                query = query.filter(operator(
                    getattr(metadata_alias, 'value_' + metadata.type),
                    value
                ))
            elif field[0] == 'ngrams': 
                query = query.filter(
                    Node.id.in_(Node_Metadata
                        .query(Node_Ngram.node_id)
                        .filter(Node_Ngram.ngram_id == Ngram.id)
                        .filter(operator(
                            getattr(Ngram, field[1]),
                            value
                        ))
                    )
                )

        # TODO: date_trunc (psql) -> index also

        # sorting
        sort_fields_names = request.DATA.get('sort', ['id'])
        if not isinstance(sort_fields_names, list):
            raise APIException('The query\'s "sort" parameter should be an array', 400)
        sort_fields_list = []
        for sort_field_name in sort_fields_names:
            try:
                desc = sort_field_name[0] == '-'
                if sort_field_name[0] in {'-', '+'}:
                    sort_field_name = sort_field_name[1:]
                field = fields_list[fields_names.index(sort_field_name)]
                if desc:
                    field = field.desc()
                sort_fields_list.append(field)
            except:
                raise APIException('Unrecognized field "%s" in the query\'s "sort" parameter. Accepted values are: "%s"' % (sort_field_name, '", "'.join(fields_names)), 400)
        query = query.order_by(*sort_fields_list)

        # pagination
        pagination = request.DATA.get('pagination', {})
        for key, value in pagination.items():
            if key not in {'limit', 'offset'}:
                raise APIException('Unrecognized parameter in "pagination": "%s"' % (key, ), 400)
            if not isinstance(value, int):
                raise APIException('In "pagination", "%s" should be an integer.' % (key, ), 400)
        if 'offset' not in pagination:
            pagination['offset'] = 0
        if 'limit' not in pagination:
            pagination['limit'] = 0


        # respond to client!
        # return DebugHttpResponse(literalquery(query))
        results = [
            dict(zip(fields_names, row))
            for row in (
                query[pagination["offset"]:pagination["offset"]+pagination["limit"]]
                if pagination['limit']
                else query[pagination["offset"]:]
            )
        ]
        pagination["total"] = query.count()
        return Response({
            "pagination": pagination,
            "retrieve": fields_names,
            "sorted": sort_fields_names,
            "results": results,
        }, 201)



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

