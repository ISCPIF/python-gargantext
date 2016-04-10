from urllib.parse import urljoin
import json
import datetime

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.exceptions import APIException
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

# 2016-03-24: refactoring, new paths
from gargantext.models.ngrams import Node, NodeNgram, Ngram
from gargantext.util.db       import session
from gargantext.util.db_cache import cache
from gargantext.util.http     import requires_auth

# from ngram.lists import listIds, listNgramIds
# from gargantext_web.db import get_or_create_node


@requires_auth
def main(request, project_id, corpus_id, document_id):
    """
    Full page view
    """
    return render_to_response('annotations/main.html', {
        # TODO use reverse()
        'api_url': urljoin(request.get_host(), '/annotations/'),
        'nodes_api_url': urljoin(request.get_host(), '/api/'),
    }, context_instance=RequestContext(request))

class NgramList(APIView):
    """Read the lists of ngrams (terms) that will become annotations"""
    renderer_classes = (JSONRenderer,)

    def get(self, request, corpus_id, doc_id):
        """Get All for a doc id"""
        corpus_id = int(corpus_id)
        doc_id = int(doc_id)

        # our results: ngrams for the corpus_id (ignoring doc_id for the moment)
        doc_ngram_list = []
        lists = {}

        for list_type in ['MAINLIST', 'MAPLIST', 'STOPLIST']:
            corpus_nod = cache.Node[corpus_id]
            list_nod = corpus_nod.children(typename=list_type).first()
            list_id = list_nod.id
            lists["%s" % list_id] = list_type

            # add to results
            doc_ngram_list += [(obj.id, obj.terms, w, list_id) for (w,obj) in list_nod.ngrams.all()]

        print("annotations.views.NgramList.doc_ngram_list: ", doc_ngram_list)
        data = { '%s' % corpus_id : {
            '%s' % doc_id :
                [
                    {'uuid': ngram_id,
                     'text': ngram_text,
                     'occurrences': ngram_occurrences,
                     'list_id': list_id,}
                for (ngram_id,ngram_text,ngram_occurrences,list_id) in doc_ngram_list
                ],
            'lists': lists
        }}

        # format alternatif de transmission des "annotations", classé par listes puis ngram_id
        # { 'corpus_id' : {
        #    list_id_stop: {term_stop1: {term_data}, term_stop2: {term_data}..},
        #    list_id_miam: {term_miam1: {term_data}, term_miam2: {term_data}..},
        #    list_id_map:  {term_map1:  {term_data}, term_map2:  {term_data}..},
        #   }
        #   'lists' : {"list_id" : "list_type" ... }
        # }

        # NB 3rd possibility: unicity of ngram_text could also allow us to use it
        #    as key and could enhance lookup later (frequent checks if term exists)
        return Response(data)


# 2016-03-24: refactoring, deactivated NgramEdit and NgramCreate
# ------------------------------------
# class NgramEdit(APIView):
#     """
#     Actions on one existing Ngram in one list
#     """
#     renderer_classes = (JSONRenderer,)
#     authentication_classes = (SessionAuthentication, BasicAuthentication)
#
#     def post(self, request, list_id, ngram_ids):
#         """
#         Edit an existing NGram in a given list
#         """
#         # implicit global session
#         list_id = int(list_id)
#         list_node = session.query(Node).filter(Node.id==list_id).first()
#         # TODO add 1 for MapList social score ?
#         if list_node.type_id == cache.NodeType['MiamList']:
#             weight=1.0
#         elif list_node.type_id == cache.NodeType['StopList']:
#             weight=-1.0
#
#         # TODO remove the node_ngram from another conflicting list
#         for ngram_id in ngram_ids.split('+'):
#             ngram_id = int(ngram_id)
#             node_ngram = NodeNgram(node_id=list_id, ngram_id=ngram_id, weight=weight)
#             session.add(node_ngram)
#
#         session.commit()
#
#         # return the response
#         return Response({
#             'uuid': ngram_id,
#             'list_id': list_id,
#             } for ngram_id in ngram_ids)
#
#     def put(self, request, list_id, ngram_ids):
#         return Response(None, 204)
#
#     def delete(self, request, list_id, ngram_ids):
#         """
#         Delete a ngram from a list
#         """
#         # implicit global session
#         print("to del",ngram_ids)
#         for ngram_id in ngram_ids.split('+'):
#             print('ngram_id', ngram_id)
#             ngram_id = int(ngram_id)
#             (session.query(NodeNgram)
#                     .filter(NodeNgram.node_id==list_id)
#                     .filter(NodeNgram.ngram_id==ngram_id).delete()
#                     )
#
#         session.commit()
#
#         # [ = = = = del from map-list = = = = ]
#         list_id = session.query(Node).filter(Node.id==list_id).first()
#         corpus = session.query(Node).filter(Node.id==list_id.parent_id , Node.type_id==cache.NodeType['Corpus'].id).first()
#         node_mapList = get_or_create_node(nodetype='MapList', corpus=corpus )
#         results = session.query(NodeNgram).filter(NodeNgram.node_id==node_mapList.id ).all()
#         ngram_2del = [int(i) for i in ngram_ids.split('+')]
#         ngram_2del_ = session.query(NodeNgram).filter(NodeNgram.node_id==node_mapList.id , NodeNgram.ngram_id.in_(ngram_2del) ).all()
#         for map_node in ngram_2del_:
#             session.delete(map_node)
#         session.commit()
#
#         node_stopList = get_or_create_node(nodetype='StopList', corpus=corpus )
#         for ngram_id in ngram_2del:
#             stop_node = NodeNgram( weight=1.0, ngram_id=ngram_id , node_id=node_stopList.id)
#             session.add(stop_node)
#         session.commit()
#         # [ = = = = / del from map-list = = = = ]
#
#         return Response(None, 204)
#
# class NgramCreate(APIView):
#     """
#     Create a new Ngram in one list
#     """
#     renderer_classes = (JSONRenderer,)
#     authentication_classes = (SessionAuthentication, BasicAuthentication)
#
#     def post(self, request, list_id):
#         """
#         create NGram in a given list
#
#         example: request.data = {'text': 'phylogeny'}
#         """
#         # implicit global session
#         list_id = int(list_id)
#         # format the ngram's text
#         ngram_text = request.data.get('text', None)
#         if ngram_text is None:
#             raise APIException("Could not create a new Ngram without one \
#                 text key in the json body")
#
#         ngram_text = ngram_text.strip().lower()
#         ngram_text = ' '.join(ngram_text.split())
#         # check if the ngram exists with the same terms
#         ngram = session.query(Ngram).filter(Ngram.terms == ngram_text).first()
#         if ngram is None:
#             ngram = Ngram(n=len(ngram_text.split()), terms=ngram_text)
#         else:
#             # make sure the n value is correct
#             ngram.n = len(ngram_text.split())
#
#         session.add(ngram)
#         session.commit()
#         ngram_id = ngram.id
#         # create the new node_ngram relation
#         # TODO check existing Node_Ngram ?
#         # £TODO ici indexation
#         node_ngram = NodeNgram(node_id=list_id, ngram_id=ngram_id, weight=1.0)
#         session.add(node_ngram)
#         session.commit()
#
#         # return the response
#         return Response({
#             'uuid': ngram_id,
#             'text': ngram_text,
#             'list_id': list_id,
#         })

class Document(APIView):
    """
    Read-only Document view, similar to /api/nodes/
    """
    renderer_classes = (JSONRenderer,)

    def get(self, request, doc_id):
        """Document by ID"""
        # implicit global session
        node = session.query(Node).filter(Node.id == doc_id).first()
        if node is None:
            raise APIException('This node does not exist', 404)

        try:
            pub_date = datetime.datetime.strptime(node.hyperdata.get('publication_date'),
                "%Y-%m-%d %H:%M:%S")
            pub_date = pub_date.strftime("%x")
        except ValueError:
            pub_date = node.hyperdata.get('publication_date')

        data = {
            'title': node.hyperdata.get('title'),
            'authors': node.hyperdata.get('authors'),
            'journal': node.hyperdata.get('journal'),
            'publication_date': pub_date,
            'full_text': node.hyperdata.get('full_text'),
            'abstract_text': node.hyperdata.get('abstract'),
            'id': node.id
        }
        return Response(data)
