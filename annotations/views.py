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

from gargantext.models.ngrams import Node, NodeNgram, Ngram, NodeNgramNgram
from gargantext.util.db       import session, aliased
from gargantext.util.db_cache import cache
from gargantext.util.http     import requires_auth
from sqlalchemy.sql.expression import case

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
        """
        Get all ngrams for a doc id, sorted by list

        NB1 : we are within a doc only
        NB2 : MAINLIST items are actually MAINLIST without MAP items
        NB3 : mostly the mainforms are in lists, but doc can have subform
              => if we simply join on ngram_id, we'll filter out the subforms
              => join on value filled by case switch:
                    (the ngram itself or a mainform if exists)
        """
        corpus_id = int(corpus_id)
        doc_id = int(doc_id)

        # our results: ngrams for the corpus_id (ignoring doc_id for the moment)
        doc_ngram_list = []
        doc_ngram_list_add = doc_ngram_list.append
        lists = {}

        corpus_nod = cache.Node[corpus_id]
        doc_nod = cache.Node[doc_id]
        scores_nod = corpus_nod.children(typename="OCCURRENCES").first()
        groups_nod = corpus_nod.children(typename="GROUPLIST").first()

        # synonyms sub table for outerjoins
        Syno = (session.query(NodeNgramNgram.ngram1_id,
                              NodeNgramNgram.ngram2_id)
                .filter(NodeNgramNgram.node_id == groups_nod.id)
                .subquery()
               )

        # maplist_ids to filter map ngrams from mainlist
        maplist_ids = {}

        # NB must do mainlist after map for filtering map items out of main
        for list_type in ['MAPLIST', 'STOPLIST', 'MAINLIST']:
            list_nod = corpus_nod.children(typename=list_type).first()
            list_id = list_nod.id
            lists["%s" % list_id] = list_type

            ListsTable = aliased(NodeNgram)

            mainform_id = case([
                                (Syno.c.ngram1_id != None, Syno.c.ngram1_id),
                                (Syno.c.ngram1_id == None, Ngram.id)
                            ])

            q = (session
                    # ngrams from the doc_id
                    .query(NodeNgram.weight, Ngram, mainform_id)
                    # debug
                    #.query(NodeNgram.weight, Ngram.terms, Ngram.id, Syno.c.ngram1_id, mainform_id)
                    .select_from(NodeNgram)
                    .join(Ngram)
                    .filter(NodeNgram.node_id == doc_id)

                    # add mainforms next to their subforms
                    .outerjoin(Syno,
                                Syno.c.ngram2_id == Ngram.id)

                    # filter mainforms on the list we want
                    .join(ListsTable,
                            #  possible that mainform is in list
                            #  and not the subform
                            ListsTable.ngram_id == mainform_id
                        )
                    .filter(ListsTable.node_id == list_id)
                )

            # add to results (and optional filtering)
            for (w,obj, mainform_id) in q.all():

                ngram_id = obj.id

                # boolean if needed
                # is_subform = (ngram_id == mainform_id)

                # special filtering case
                # when MAINLIST requested we actually want MAIN without MAP
                if list_type == "MAPLIST":
                    maplist_ids[ngram_id] = True
                if list_type == "MAINLIST":
                    if ngram_id in maplist_ids:
                        # skip object
                        continue

                # normal case
                doc_ngram_list_add((ngram_id, obj.terms, w, list_id))

        # debug
        # print("annotations.views.NgramList.doc_ngram_list: ", doc_ngram_list)
        data = { '%s' % corpus_id : {
            '%s' % doc_id :
                [
                    {'uuid': ngram_id,
                     'text': ngram_text,
                     'occs': ngram_occurrences,
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
