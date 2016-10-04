from django.core.exceptions import *
from .api import * #APIView, APIException entre autres
from gargantext.util.db import session
from gargantext.models import Node
from gargantext.util.http import *

class CorpusView(APIView):
    '''API endpoint that represent a corpus'''
    def get(self, request, project_id, corpus_id, view = "DOCUMENT"):
        '''GET corpus detail
        default view full documents
        '''
        params = get_parameters(request)
        if "view" in params.keys():
            filter_view = params["view"].upper()
            if view in ["DOCUMENT", "JOURNAL", "TITLE", "ANALYTICS", "RESSOURCE"]:
                view = filter_view

        project = session.query(Node).filter(Node.id == project_id, Node.typename == "PROJECT").first()
        check_rights(request, project.id)
        if project is None:
            return Response({'detail' : "PROJECT Node #%s not found" %(project_id) },
                                  status = status.HTTP_404_NOT_FOUND)

        corpus = session.query(Node).filter(Node.id == corpus_id, Node.typename == "CORPUS").first()
        if corpus is None:
            return Response({'detail' : "CORPUS Node #%s not found" %(corpus_id) },
                                  status = status.HTTP_404_NOT_FOUND)




        documents = session.query(Node).filter(Node.parent_id == corpus_id, Node.typename == view).all()

        context = format_response(corpus, documents)
        return Response(context)

    def delete(self, request, project_id,  corpus_id):
        '''DELETE corpus'''
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>delete")

        # project = session.query(Node).filter(Node.id == project_id, Node.typename == "PROJECT").first()
        # check_rights(request, project.id)
        # if project is None:
        #     return Response({'detail' : "PROJECT Node #%s not found" %(project_id) },
        #                           status = status.HTTP_404_NOT_FOUND)

        corpus = session.query(Node).filter(Node.id == corpus_id, Node.typename == "CORPUS").first()
        if corpus is None:
            return Response({'detail' : "CORPUS Node #%s not found" %(corpus_id) },
                                  status = status.HTTP_404_NOT_FOUND)

        documents = session.query(Node).filter(Node.parent_id == corpus_id).all()
        session.delete(documents)
        session.delete(corpus)

        session.commit()
        return Response(detail="Deleted corpus #%s" %str(corpus_id), status=HTTP_204_NO_CONTENT)

    def put(self, request, project_id, corpus_id, view="DOCUMENT"):
        '''UPDATE corpus'''
        project = session.query(Node).filter(Node.id == project_id, Node.typename == "PROJECT").first()
        project = check_rights(request, project.id)
        if project is None:
            return Response({'detail' : "PROJECT Node #%s not found" %(project_id) },
                                  status = status.HTTP_404_NOT_FOUND)

        corpus = session.query(Node).filter(Node.id == corpus_id, Node.typename == "CORPUS").first()
        if corpus is None:
            return Response({'detail' : "CORPUS Node #%s not found" %(corpus_id) },
                                  status = status.HTTP_404_NOT_FOUND)


        #documents = session.query(Node).filter(Node.parent_id == corpus_id, Node.typename= view).all()
        for key, val in request.data.items():
            if key in ["name", "date", "username", "hyperdata"]:
                if key == "username":
                    #changement de propriétaire
                    #user = session.query(Node).filter(Node.typename=="USER", Node.username== username).first()
                    #print(user)
                    #set(node, user_id, user.id)
                    pass
                elif key == "hyperdata":
                    #updating some contextualvalues of the corpus
                    pass
                else:
                    setattr(node, key, val)
        session.add(node)
        session.commit()
        '''#updating children???

        '''
        return Response({"detail":"Updated corpus #" %str(corpus.id)}, status=HTTP_202_ACCEPTED)

    def post(self, request, project_id, corpus_id):
        '''ADD a new RESOURCE to CORPUS'''
        project = session.query(Node).filter(Node.id == project_id, Node.typename == "PROJECT").first()
        check_rights(request, project.id)
        if project is None:
            return Response({'detail' : "PROJECT Node #%s not found" %(project_id) },
                                  status = status.HTTP_404_NOT_FOUND)

        corpus = session.query(Node).filter(Node.id == corpus_id, Node.typename == "CORPUS").first()
        if corpus is None:
            return Response({'detail' : "CORPUS Node #%s not found" %(corpus_id) },
                                  status = status.HTTP_404_NOT_FOUND)
