from urllib.parse import urljoin
import json
import datetime

from django.shortcuts import render
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
def main(request, project_id, corpus_id, document_id, optional_focus_ngram):
    """
    Full page view

    NB: url params are NOT used here (angular has its own url regex in app.js)
    """
    context = { 'api_url'      : urljoin(request.get_host(), '/annotations/')
              , 'garg_url'     : request.get_host()
              , 'nodes_api_url': urljoin(request.get_host(), '/api/')
              }
    return render(request, 'annotations/main.html', context)

class NgramList(APIView):
    """Read the lists of ngrams (terms) that will become annotations"""
    renderer_classes = (JSONRenderer,)

    def get(self, request, corpus_id, doc_id):
        """
        Get all ngrams for a doc id, sorted by list

        usual route: /annotations/documents/<docid>

        NB1 : we are within a doc only
        NB2 : MAINLIST items are actually MAINLIST without MAP items
        NB3 : mostly the mainforms are in lists, but doc can have subform
              => if we simply join on ngram_id, we'll filter out the subforms
              => join on value filled by case switch:
                    (the ngram itself or a mainform if exists)
        """
        corpus_id = int(corpus_id)
        doc_id = int(doc_id)

        # our results: ngrams within a doc and a list + weights in the doc
        doc_ngram_list = []
        doc_ngram_list_add = doc_ngram_list.append
        lists = {}

        corpus_nod = cache.Node[corpus_id]
        doc_nod = cache.Node[doc_id]
        # scores_nod = corpus_nod.children(typename="OCCURRENCES").first()
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

                if mainform_id == ngram_id:
                    group = None
                else:
                    group = mainform_id
                # normal case
                doc_ngram_list_add((ngram_id, obj.terms, group, w, list_id))

        # debug
        # print("annotations.views.NgramList.doc_ngram_list: ", doc_ngram_list)
        data = { '%s' % corpus_id : {
            '%s' % doc_id :
                [
                    {'uuid': ngram_id,
                     'group': group,      # the mainform if there is a group
                     'text': ngram_text,
                     'occs': ngram_occs,
                     'list_id': list_id,}
                for (ngram_id,ngram_text,group,ngram_occs,list_id) in doc_ngram_list
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
# 2016-07-21: removed NgramCreate: replaced the local httpservice by api/ngrams (put)

class Document(APIView):
    """
    Read-only Document view, similar to /api/nodes/
    """
    renderer_classes = (JSONRenderer,)

    def get(self, request, doc_id):
        """Document by ID"""
        node = session.query(Node).filter(Node.id == doc_id).first()
        corpus = session.query(Node).filter(Node.id == node.parent_id).first()
        corpus_workflow_status = corpus.hyperdata['statuses'][0]
        if node is None:
            raise APIException('This node does not exist', 404)

        try:
            pub_date = datetime.datetime.strptime(node.hyperdata.get('publication_date'),
                "%Y-%m-%d %H:%M:%S")
            pub_date = pub_date.strftime("%x")
        except ValueError:
            pub_date = node.hyperdata.get('publication_date')

        data = {
            'corpus_status': corpus_workflow_status,
            'title': node.hyperdata.get('title'),
            'authors': node.hyperdata.get('authors'),
            'source': node.hyperdata.get('source'),
            'publication_date': pub_date,
            'full_text': node.hyperdata.get('full_text'),
            'abstract_text': node.hyperdata.get('abstract'),
            'id': node.id
        }
        return Response(data)
