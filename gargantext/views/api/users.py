from .api import * #notamment APIView, check_rights, format_response
from gargantext.util.http import *
from django.core.exceptions import *
from collections import defaultdict
from gargantext.util.toolchain import  *
import copy
from gargantext.util.db import session

class UserParameters(APIView):
    '''API endpoint that represent the parameters of the user'''
    def get(self, request):
        node_user = session.query(Node).filter(Node.user_id == request.user.id, Node.typename== "USER").first()
        if node_user is None:
            return Response({"detail":"Not Found"}, status=HTTP_404)
        else:
            #context = format_response(node_user, )
            return Response(node_user.hyperdata)


    def put(self, request):
        if request.user.id is None:
            raise TypeError("This API request must come from an authenticated user.")
        else:
            # we query among the nodes that belong to this user
            user = cache.User[request.user.id]
        node_user = session.query(Node).filter(Node.user_id == user.id, Node.typename== "USER").first()
        if node_user is None:
            return Response({"detail":"Not Allowed"}, status=HTTP_401_UNAUTHORIZED)

        for k, v in request.data.items():
            node_user.hyperdata[k] =  v
            # setattr(node_user.hyperdata, k, v)
            # print(node_user.hyperdata)
        node_user.save_hyperdata()
        session.add(node_user)
        session.commit()
        node_user = session.query(Node).filter(Node.user_id == user.id, Node.typename== "USER").first()
        print(node_user.hyperdata)
        return Response({"detail":"Updated user parameters", "hyperdata": node_user.hyperdata}, status=HTTP_202_ACCEPTED)
