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

from node.models import Node
from gargantext_web.db import *
from ngram.lists import listIds, listNgramIds, ngramList

import sqlalchemy
from sqlalchemy.orm import aliased


@login_required
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
    """Read and Write Annotations"""
    renderer_classes = (JSONRenderer,)

    def get(self, request, corpus_id, doc_id):
        """Get All for a doc id"""
        lists = dict()
        for list_type in ['MiamList', 'StopList']:
            list_id = list()
            list_id = listIds(user_id=request.user.id, corpus_id=int(corpus_id), typeList=list_type)
            lists["%s" % list_id[0][0]] = list_type

        # ngrams of list_id of corpus_id:
        doc_ngram_list = listNgramIds(corpus_id=corpus_id, doc_id=doc_id, user_id=request.user.id)
        data = { '%s' % corpus_id : {
            '%s' % doc_id : [
                {
                    'uuid': ngram_id,
                    'text': ngram_text,
                    'occurrences': ngram_occurrences,
                    'list_id': list_id,
                }
                for ngram_id, ngram_text, ngram_occurrences, list_id in doc_ngram_list],
            'lists': lists
        }}
        return Response(data)


class Ngram(APIView):
    """
    Actions on one Ngram in one list
    """

    def post(self, request, list_id, ngram_id):
        """
        Add a ngram in a list
        """
        ngram_dict = json.loads(request.POST.get('annotation'))
        if ngram_id == 'new':
            ngram_dict = json.loads(request.POST.get('annotation'))
            results = ngramList('create', list_id, ngram_ids=[ngram_dict['text']])
        else:
            results = ngramList('add', list_id, ngram_ids=[ngram_id])

        return Response([{
                'uuid': ngram_id,
                'text': ngram_text,
                'occurrences': ngram_occurrences,
                'list_id': list_id,

            } for ngram_id, ngram_text, ngram_occurrences in results])

    def delete(self, request, list_id, ngram_id):
        """
        Delete a ngram from a list
        """
        return Response({ 'delete' : { '%s' % ngram_id :
                ngramList(do='del', ngram_ids=[ngram_id], list_id=list_id)}})


class Document(APIView):
    """
    Read-only Document view, similar to /api/nodes/
    """
    renderer_classes = (JSONRenderer,)

    def get(self, request, doc_id):
        """Document by ID"""
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
