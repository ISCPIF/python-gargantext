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
from gargantext.models import Node, ProjectNode, DocumentNode
from gargantext.util.db import session, get_engine
from collections import Counter
import importlib
from django.http import Http404

# Import those to be available by notebook user
from langdetect import detect as detect_lang
from gargantext.models import UserNode, User


class NotebookError(Exception):
    pass


def documents(corpus_id):
    return (session.query(DocumentNode).filter_by(parent_id=corpus_id)
                  #.order_by(Node.hyperdata['publication_date'])
                   .all())


#import seaborn as sns
import pandas as pd

def chart(docs, field):
    year_publis = list(Counter([doc.hyperdata[field] for doc in docs]).items())
    frame0 = pd.DataFrame(year_publis, columns=['Date', 'DateValue'])
    frame1 = pd.DataFrame(year_publis, columns=['Date', 'DateValue'], index=frame0.Date)
    return frame1


from gargantext.util.crawlers.HAL import HalCrawler

def scan_hal(request):
    hal = HalCrawler()
    return hal.scan_results(request)


def scan_gargantext(corpus_id, request):
    return (session.query(DocumentNode)
                   .filter_by(parent_id=corpus_id)
                   .filter(Node.title_abstract.match(request))
                   .count())


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
