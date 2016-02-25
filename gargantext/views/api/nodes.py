from gargantext.util.http import *
from gargantext.util.db import *
from gargantext.util.db_cache import *
from gargantext.models import *
from gargantext.constants import *

from gargantext.util.validation import validate


class NodeListResource(APIView):

    _fields = ['id', 'parent_id', 'name', 'typename', 'hyperdata']
    _types = NODETYPES

    def _query(self, request):
        # parameters validation
        parameters = get_parameters(request)
        parameters = validate(parameters, {'type': dict, 'items': {
            'pagination_limit': {'type': int, 'default': 10},
            'pagination_offset': {'type': int, 'default': 0},
            'fields': {'type': list, 'default': self._fields, 'items': {
                'type': str, 'range': self._fields,
            }},
            # optional filtering parameters
            'type': {'type': list, 'default': self._types, 'required': False, 'items': {
                'type': str, 'range': self._types,
            }},
            'parent_id': {'type': int, 'required': False},
        }})
        # start the query
        query = session.query(*tuple(
            getattr(Node, field) for field in parameters['fields']
        ))
        # filter by type
        if 'type' in parameters:
            query = query.filter(Node.typename.in_(parameters['type']))
        # filter by parent
        if 'parent_id' in parameters:
            query = query.filter(Node.parent_id == parameters['parent_id'])
        # count
        count = query.count()
        # order
        query = query.order_by(Node.hyperdata['publication_date'], Node.id)
        # paginate the query
        if parameters['pagination_limit'] == -1:
            query = query[parameters['pagination_offset']:]
        else:
            query = query[
                parameters['pagination_offset'] :
                parameters['pagination_limit']
            ]
        # return the result!
        return parameters, query, count

    def get(self, request):
        """Displays the list of nodes corresponding to the query.
        """
        parameters, query, count = self._query(request)
        return JsonHttpResponse({
            'parameters': parameters,
            'count': count,
            'records': [dict(zip(parameters['fields'], node)) for node in query]
        })

    def post(self, request):
        pass

    def delete(self, request):
        """Removes the list of nodes corresponding to the query.
        WARNING! THIS IS TOTALLY UNTESTED!!!!!
        """
        parameters, query, count = self._query(request)
        for node in query:
            node.delete()
        session.commit()
        return JsonHttpResponse({
            'parameters': parameters,
            'count': count,
        }, 200)


class NodeResource(APIView):

    def _query(self, request, node_id):
        user = cache.User[request.user.username]
        node = session.query(Node).filter(Node.id == node_id).first()
        if node is None:
            raise Http404()
        if not user.owns(node):
            raise HttpResponseForbidden()
        return user, node

    def get(self, request, node_id):
        user, node = self._query(request, node_id)
        return JsonHttpResponse({
            'id': node.id,
            'parent_id': node.parent_id,
            'name': node.name,
            'hyperdata': node.hyperdata,
        })

    def delete(self, request, node_id):
        from sqlalchemy import delete
        user, node = self._query(request, node_id)
        result = session.execute(
            delete(Node).where(Node.id == node_id)
        )
        session.commit()
        return JsonHttpResponse({'deleted': result.rowcount})
