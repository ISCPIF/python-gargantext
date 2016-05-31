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
from gargantext.util.db       import session, aliased
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
        'garg_url': request.get_host(),
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

        corpus_nod = cache.Node[corpus_id]
        doc_nod = cache.Node[doc_id]
        scores_nod = corpus_nod.children(typename="OCCURRENCES").first()

        for list_type in ['MAINLIST', 'MAPLIST', 'STOPLIST']:
            list_nod = corpus_nod.children(typename=list_type).first()
            list_id = list_nod.id
            lists["%s" % list_id] = list_type

            ListsTable = aliased(NodeNgram)

            # doc_nod.ngrams iff we just need the occurrences in the doc (otherwise do manually)
            q = doc_nod.ngrams.join(ListsTable).filter(ListsTable.node_id == list_id)

            # add to results
            doc_ngram_list += [(obj.id, obj.terms, w, list_id) for (w,obj) in q.all()]

        # debug
        # print("annotations.views.NgramList.doc_ngram_list: ", doc_ngram_list)
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
# 2016-05-27: removed NgramEdit: replaced the local httpservice by api/ngramlists
# ------------------------------------
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
