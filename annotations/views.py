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
from sqlalchemy.orm import aliased


def main(request, project_id, corpus_id, document_id):
    """Demo page, temporary"""
    return render_to_response('annotations/main.html', {
        # TODO use reverse()
        'api_url': urljoin(request.get_host(), '/annotations/'),
        'nodes_api_url': urljoin(request.get_host(), '/api/')
    }, context_instance=RequestContext(request))


class NgramList(APIView):
    """Read and Write Annotations"""
    renderer_classes = (JSONRenderer,)

    def get(self, request, corpus_id, doc_id):
        """Get All for a doc id"""
        # ngrams of list_id of corpus_id:
        doc_ngram_list = listNgramIds(corpus_id=corpus_id, doc_id=doc_id, user_id=request.user.id)
        data = { '%s' % corpus_id : { '%s' % doc_id : [
            {
                'uuid': ngram_id,
                'text': ngram_text,
                'occurrences': ngram_occurrences,
                'list_id': list_id,
            }
            for ngram_id, ngram_text, ngram_occurrences, list_id in doc_ngram_list]
        }}
        return Response(data)


class Ngram(APIView):
    """Action on one Ngram in one list"""
    def post(self, request, list_id, ngram_id):
        """
        Add a ngram in a list
        """
        ngramList(do='add', ngram_ids=[ngram_id], list_id=list_id)

    def delete(self, request, list_id, ngram_id):
        """
        Remove a ngram from a list
        """
        ngramList(do='del', ngram_ids=[ngram_id], list_id=list_id)


class CorpusList(APIView):
    #authentication_classes = (SessionAuthentication, BasicAuthentication)
    # TODO: Be carefull need authentication!

    def get(self, request, corpus_id):
        """
        Return all lists associated with a corpus
        """
        user_id = session.query(User.id).filter(User.username==str(request.user)).first()[0]
        lists = dict()

        for list_type in ['MiamList', 'StopList']:
            list_id = list()
            list_id = listIds(user_id=user_id, corpus_id=int(corpus_id), typeList=list_type)
            lists[list_type] = int(list_id[0][0])
#            lists[list_type]['id']['name'] = r[0][1]

        return JsonHttpResponse({
            'MiamList' : lists['MiamList'],
            'StopList' : lists['StopList']
         })

class Document(APIView):
    """Read-only Document"""
    renderer_classes = (JSONRenderer,)

    def get(self, request, doc_id):
        """Document by ID"""
        node = session.query(Node).filter(Node.id == doc_id).first()
        if node is None:
            raise APIException('This node does not exist', 404)

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
