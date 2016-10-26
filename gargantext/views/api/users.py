from .api import * #notamment APIView, check_rights, format_response
from gargantext.util.http import *
from django.core.exceptions import *
from collections import defaultdict
from gargantext.util.toolchain import  *
import copy
from gargantext.util.db import session

class UserItem(APIView):
    '''API endpoint that represent the parameters of the user'''
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
            setattr(node_user.hyperdata, key, val)

        session.add(node_user)
        session.commit()
        return Response({"detail":"Updated user parameters"}, status=HTTP_202_ACCEPTED)
