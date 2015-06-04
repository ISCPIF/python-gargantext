from urllib.parse import urljoin
import json

from django.shortcuts import render_to_response
from django.template import RequestContext

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

from node.models import Node
from gargantext_web.db import *

from ngram.lists import listIds, listNgramIds, ngramList
import sqlalchemy
from sqlalchemy.sql import func
from sqlalchemy import desc, asc, or_, and_, Date, cast, select
from sqlalchemy import literal_column
from sqlalchemy.orm import aliased



def demo(request):
    """Demo page, temporary"""
    return render_to_response('annotations/demo.html', {
        'api_url': urljoin(request.get_host(), '/annotations/')
    }, context_instance=RequestContext(request))


# This class below is a duplicate with the class Nodes in
# /srv/gargantext/gargantext_web/api.py
# All information you need from Nodes in api.py is in hyperdata
# You may modify api.py (keeping compatibility) for your own needs
# See in urls the url pattern to use
class Document(APIView):
    """Read-only Document"""
    renderer_classes = (JSONRenderer,)

    def get(self, request, doc_id):
        """Document by ID"""
        node = session.query(Node).filter(Node.id == doc_id).first()
        # TODO 404 if not Document or ID not found
        data = {
            'title': node.hyperdata.get('title'),
            'authors': node.hyperdata.get('authors'),
            'journal': node.hyperdata.get('journal'),
            'publication_date': node.hyperdata.get('publication_date'),
            'full_text': node.hyperdata.get('full_text'),
            'abstract_text': node.hyperdata.get('abstract'),
            'id': node.id,
            'current_page_number': 4, # TODO remove, this is client side
            'last_page_number': 30 # TODO remove, this is client side
        }
        # return formatted result
        return Response(data)

class NgramList(APIView):
    """Read and Write Annotations"""
    renderer_classes = (JSONRenderer,)

    def get(self, request, list_id):
        """Get All for on List ID"""
        doc_id = request.GET.get('docId')
        # TODO DB query
        # Example with 'MiamList', same with 'StopList'
        corpus_id = session.query(Node.parent_id).filter(Node.id == doc_id).first()
        miamlist_ids = listIds(user_id=request.user.id,
                              corpus_id=corpus_id,
                              typeList='MiamList')

        miamlist_id, miamlist_name = miamlist_ids[0]

        # ngrams of list_id of corpus_id:
        corpus_ngram_miam_list = listNgramIds(list_id=miamList_id)

        # ngrams of list_id of corpus_id:
        doc_ngram_miam_list = listNgramIds(list_id=miamList_id, doc_id=doc_id)

        # now you can model your dict as you want (for doc or corpus level):
        ngram_id, ngram_text, ngram_occurrences = doc_ngram_miam_list[0]

        data = { '%s' % list_id : { '%s' % doc_id : [
            {
                'uuid': '1',
                'text': 'what',
                'category': 'stoplist',
                'level': 'global',
                'occurrences': 1
            },
            {
                'uuid': '2',
                'text': 'rotations',
                'category': 'miamlist',
                'level': 'local',
                'occurrences': 1
            },
            {
                'uuid': '3',
                'text': 'etsy',
                'category': 'stoplist',
                'level': 'local',
                'occurrences': 1
            },
            {
                'uuid': '4',
                'text': 'employees',
                'category': 'miamlist',
                'level': 'local',
                'occurrences': 1
            },
            {
                'uuid': '5',
                'text': '2010',
                'category': 'stoplist',
                'level': 'global',
                'occurrences': 1
            },
            {
                'uuid': '6',
                'text': 'stoplist keyword',
                'category': 'stoplist',
                'level': 'local',
                'occurrences': 255
            },
            {
                'uuid': '7',
                'text': 'another stoplist keyword',
                'category': 'stoplist',
                'level': 'local',
                'occurrences': 23
            },
            {
                'uuid': '8',
                'text': 'dmc-gm5',
                'category': 'miamlist',
                'level': 'local',
                'occurrences': 1
            },
            {
                'uuid': '9',
                'text': 'scale of the GM-series',
                'category': 'miamlist',
                'level': 'local',
                'occurrences': 1
            },
            {
                'uuid': '10',
                'text': 'engineering rotations',
                'category': 'miamlist',
                'level': 'local',
                'occurrences': 1
            },
            {
                'uuid': '11',
                'text': 'pixel electronic viewfinder',
                'category': 'miamlist',
                'level': 'local',
                'occurrences': 1
            },
            {
                'uuid': '12',
                'text': 'viewfinder',
                'category': 'miamlist',
                'level': 'local',
                'occurrences': 1
            },
            {
                'uuid': '13',
                'text': 'pixel electronic',
                'category': 'miamlist',
                'level': 'local',
                'occurrences': 1
            },
            {
                'uuid': '14',
                'text': 'GM',
                'category': 'miamlist',
                'level': 'local',
                'occurrences': 1
            },
            {
                'uuid': '15',
                'text': 'support rotations',
                'category': 'miamlist',
                'level': 'local',
                'occurrences': 1
            },
            {
                'uuid': '16',
                'text': 'miamlist keyword',
                'category': 'miamlist',
                'level': 'local',
                'occurrences': 1
            },
            {
                'uuid': '17',
                'text': 'miamlist keyword',
                'category': 'miamlist',
                'level': 'local',
                'occurrences': 1
            },
            {
                'uuid': '18',
                'text': 'another miamlist keyword',
                'category': 'miamlist',
                'level': 'local',
                'occurrences': 3
            }
        ]}}
        return Response(data)


class Ngram(APIView):
    """Read and Write Annotations"""
    renderer_classes = (JSONRenderer,)

    def delete(self, request, list_id, ngram_id):
        """
        TODO Delete one annotation by id
        associated with one Document (remove edge)
        """
        doc_id = request.GET.get('docId')
        annotationId = request.GET.get("annotationId")
        print(annotationDict)
        # TODO DB query
        # Use the ngramList function in ngram.lists.py for that
        # It can return True or False
        ngramList(do='del', ngram_ids=[ngram_id,], list_id=list_id)

        return Response({})

    def post(self, request, list_id, ngram_id):
        """
        TODO update one annotation (document level)
        associated with one Document (add edge)
        """
        doc_id = request.GET.get('docId')
        annotationDict = json.loads(request.POST.get("annotation"))
        print(annotationDict)
        # TODO DB query
        return Response(annotationDict)
