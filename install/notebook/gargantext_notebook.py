#!/usr/bin/env python
"""
   Gargantext Software Copyright (c) 2016-2017 CNRS ISC-PIF -
http://iscpif.fr
    Licence (see :
http://gitlab.iscpif.fr/humanities/gargantext/blob/stable/LICENSE )
    - In France : a CECILL variant affero compliant
    - GNU aGPLV3 for all other countries
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gargantext.settings')
django.setup()

from gargantext.constants import QUERY_SIZE_N_MAX, get_resource, get_resource_by_name
from gargantext.models import (Node, ProjectNode, DocumentNode,
                               Ngram, NodeNgram, NodeNgramNgram, NodeNodeNgram)
from gargantext.util.db import session, get_engine, func, aliased, case
from collections import Counter
import importlib
from django.http import Http404

# Import those to be available by notebook user
from langdetect import detect as detect_lang
from gargantext.models import UserNode, User
import functools

class NotebookError(Exception):
    pass


def documents(corpus_id):
    return (session.query(DocumentNode).filter_by(parent_id=corpus_id)
                  #.order_by(Node.hyperdata['publication_date'])
                   .all())


#import seaborn as sns
import pandas as pd

def countByField(docs, field):
    return list(Counter([doc.hyperdata[field] for doc in docs]).items())

def chart(docs, field):
    year_publis = countByField(docs, field)
    frame0 = pd.DataFrame(year_publis, columns=['Date', 'DateValue'])
    frame1 = pd.DataFrame(year_publis, columns=['Date', 'DateValue'], index=frame0.Date)
    return frame1


from gargantext.util.crawlers.HAL import HalCrawler

def scan_hal(request):
    hal = HalCrawler()
    return hal.scan_results(request)


def _search_docs(corpus_id, request, fast=False):
    q = session.query(DocumentNode).filter_by(parent_id=corpus_id)

    # Search ngram <request> in hyperdata <field>
    H = lambda field, request: Node.hyperdata[field].astext.op('~*')(request)

    if not fast:
        # Only match <request> starting and ending with word boundary
        # Sequence of spaces will match any sequence of spaces
        request = '\s+'.join(filter(None, r'\m{}\M'.format(request).split(' ')))

    return q.filter(Node.title_abstract.match(request)) if fast else \
           q.filter(H('title', request) | H('abstract', request))


def scan_gargantext(corpus_id, request, fast=False, documents=False):
    query = _search_docs(corpus_id, request, fast)

    if documents:
        return query.all()

    return query.with_entities(func.count(DocumentNode.id.distinct())).one()[0]


def scan_gargantext_and_delete(corpus_id, request, fast=False):
    r = _search_docs(corpus_id, request, fast).delete(synchronize_session='fetch')
    session.commit()

    return r


def myProject_fromUrl(url):
    """
    myProject :: String -> Project
    """
    project_id = url.split("/")[4]
    project = session.query(ProjectNode).get(project_id)
    return project


def newCorpus(project, source, name=None, query=None):
    error = False

    if name is None:
        name = query

    if not isinstance(project, ProjectNode):
        error = "a valid project"
    if not isinstance(source, int) and not isinstance(source, str):
        error = "a valid source identifier: id or name"
    elif not isinstance(query, str):
        error = "a valid query"
    elif not isinstance(name, str):
        error = "a valid name"

    if error:
        raise NotebookError("Please provide %s." % error)

    resource = get_resource(source) if isinstance(source, int) else \
               get_resource_by_name(source)

    moissonneur_name = get_moissonneur_name(resource) if resource else \
                       source.lower()

    try:
        moissonneur = get_moissonneur(moissonneur_name)
    except ImportError:
        raise NotebookError("Invalid source identifier: %r" % source)

    return run_moissonneur(moissonneur, project, name, query)


def get_moissonneur_name(ident):
    """ Return moissonneur module name from RESOURCETYPE or crawler name """

    # Does it quacks like a RESOURCETYPE ?
    if hasattr(ident, 'get'):
        ident = ident.get('crawler')

    # Extract name from crawler class name, otherwise assume ident is already
    # a moissonneur name.
    if isinstance(ident, str) and ident.endswith('Crawler'):
        return ident[:-len('Crawler')].lower()


def get_moissonneur(name):
    """ Return moissonneur module from its name """
    if not isinstance(name, str) or not name.islower():
        raise NotebookError("Invalid moissonneur name: %r" % name)

    module = importlib.import_module('moissonneurs.%s' % name)
    module.name = name

    return module


def run_moissonneur(moissonneur, project, name, query):
    """ Run moissonneur and return resulting corpus """

    # XXX Uber-kludge with gory details. Spaghetti rulezzzzz!
    class Dummy(object):
        pass

    request = Dummy()
    request.method = 'POST'
    request.path = 'nowhere'
    request.META = {}
    # XXX 'string' only have effect on moissonneurs.pubmed; its value is added
    #     when processing request client-side, take a deep breath and see
    #     templates/projects/project.html for more details.
    request.POST = {'string': name,
                    'query': query,
                    'N': QUERY_SIZE_N_MAX}
    request.user = Dummy()
    request.user.id = project.user_id
    request.user.is_authenticated = lambda: True

    if moissonneur.name == 'istex':
        # Replace ALL spaces by plus signs
        request.POST['query'] = '+'.join(filter(None, query.split(' ')))

    try:
        import json

        r = moissonneur.query(request)
        raw_json = r.content.decode('utf-8')
        data = json.loads(raw_json)

        if moissonneur.name == 'pubmed':
            count = sum(x['count'] for x in data)
            request.POST['query'] = raw_json
        elif moissonneur.name == 'istex':
            count = data.get('total', 0)
        else:
            count = data.get('results_nb', 0)

        if count > 0:
            corpus = moissonneur.save(request, project.id, return_corpus=True)
        else:
            return None

    except (ValueError, Http404) as e:
        raise e

    # Sometimes strange things happens...
    if corpus.name != name:
        corpus.name = name
        session.commit()

    return corpus


ALL_LIST_TYPES = ['main', 'map', 'stop']


def _ngrams(corpus_id, list_types, entities):
    list_types = (list_types,) if isinstance(list_types, str) else list_types
    list_typenames = [
        '{}LIST'.format(t.upper()) for t in list_types if t in ALL_LIST_TYPES]

    # `Node` is our list, ie. MAINLIST and/or MAPLIST and/or STOPLIST
    return (session.query(*entities)
                   .select_from(Ngram)
                   .filter(NodeNgram.ngram_id==Ngram.id,
                           NodeNgram.node_id==Node.id,
                           Node.parent_id==corpus_id,
                           Node.typename.in_(list_typenames)))


def corpus_list(corpus_id, list_types=ALL_LIST_TYPES, with_synonyms=False,
                with_count=False):
    # Link between a GROUPLIST, a normal form (ngram1), and a synonym (ngram2)
    NNN = NodeNgramNgram

    # Get the list type from the Node type -- as in CSV export
    list_type = (case([(Node.typename=='MAINLIST', 'main'),
                       (Node.typename=='MAPLIST',  'map'),
                       (Node.typename=='STOPLIST', 'stop')])
                 .label('type'))

    # We will retrieve each ngram as the following tuple:
    entities = (list_type, Ngram.terms.label('ng'))

    if with_count:
        entities += (Ngram.id.label('id'),)

    # First, get ngrams from wanted lists
    ngrams = _ngrams(corpus_id, list_types, entities)

    # Secondly, exclude "synonyms" (grouped ngrams that are not normal forms).
    # We have to exclude synonyms first because data is inconsistent and some
    # of them can be both in GROUPLIST and in MAIN/MAP/STOP lists. We want to
    # take synonyms from GROUPLIST only -- see below.
    Groups = aliased(Node, name='groups')
    query = (ngrams.outerjoin(Groups, (Groups.parent_id==corpus_id) & (Groups.typename=='GROUPLIST'))
                   .outerjoin(NNN, (NNN.node_id==Groups.id) & (NNN.ngram2_id==Ngram.id))
                   .filter(NNN.ngram1_id==None))

    # If `with_synonyms` is True, add them from GROUPLIST: this is the reliable
    # source for them
    if with_synonyms:
        Synonym = aliased(Ngram)
        ent = (list_type, Synonym.terms.label('ng'), Synonym.id.label('id'))
        synonyms = (ngrams.with_entities(*ent)
                          .filter(NNN.ngram1_id==Ngram.id,
                                  NNN.ngram2_id==Synonym.id,
                                  NNN.node_id==Groups.id,
                                  Groups.parent_id==corpus_id,
                                  Groups.typename=='GROUPLIST'))
        query = query.union(synonyms)

    # Again, data is inconsistent: MAINLIST may intersect with MAPLIST and
    # we don't wan't that
    if 'main' in list_types and 'map' not in list_types:
        # Exclude MAPLIST ngrams from MAINLIST
        query = query.except_(_ngrams(corpus_id, 'map', entities))

    if with_count:
        N = query.subquery()
        return (session.query(N.c.type, N.c.ng, NodeNodeNgram.score)
                       .join(Node, (Node.parent_id==corpus_id) & (Node.typename=='OCCURRENCES'))
                       .outerjoin(NodeNodeNgram, (NodeNodeNgram.ngram_id==N.c.id) &
                                                 (NodeNodeNgram.node1_id==Node.id) &
                                                 (NodeNodeNgram.node2_id==corpus_id)))

    # Return found ngrams sorted by list type, and then alphabetically
    return query.order_by('type', 'ng')
