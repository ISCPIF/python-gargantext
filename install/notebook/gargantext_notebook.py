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
from gargantext.models import ProjectNode, DocumentNode, UserNode, User
from gargantext.util.db import session, get_engine
from collections import Counter
import importlib
from django.http import Http404


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


def scan_gargantext(corpus_id, lang, request):
    connection = get_engine().connect()
    # TODO add some sugar the request (ideally request should be the same for hal and garg)
    query = """select count(n.id) from nodes n
                  where to_tsvector('%s', hyperdata ->> 'abstract' || 'title')
                  @@ to_tsquery('%s')
                  AND n.parent_id = %s;""" % (lang, request, corpus_id)
    return [i for i in connection.execute(query)][0][0]
    connection.close()


def myProject_fromUrl(url):
    """
    myProject :: String -> Project
    """
    project_id = url.split("/")[4]
    project = session.query(ProjectNode).get(project_id)
    return project


def newCorpus(project, resource=11, name="Machine learning", query="LSTM"):
    error = False

    if not isinstance(project, ProjectNode):
        error = "a valid project"
    if not isinstance(resource, int) and not isinstance(resource, str):
        error = "a valid resource identifier: id or name"
    elif not isinstance(name, str):
        error = "a valid name"
    elif not isinstance(query, str):
        error = "a valid query"

    if error:
        raise NotebookError("Please provide %s." % error)

    source = get_resource(resource) if isinstance(resource, int) else \
             get_resource_by_name(resource)

    moissonneur_name = get_moissonneur_name(source) if source else \
                       resource.lower()

    try:
        moissonneur = get_moissonneur(moissonneur_name)
    except ImportError:
        raise NotebookError("Invalid resource identifier: %r" % resource)

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
    return importlib.import_module('moissonneurs.%s' % name)


def run_moissonneur(moissonneur, project, name, query):
    """ Run moissonneur and return resulting corpus """

    # XXX Uber-kludge with gory details. Spaghetti rulezzzzz!
    class Dummy(object):
        pass

    request = Dummy()
    request.method = 'POST'
    request.path = 'nowhere'
    request.META = {}
    request.POST = {'string': name,
                    'query': query,
                    'N': QUERY_SIZE_N_MAX}
    request.user = (session.query(UserNode).join(User)
                           .filter(User.username=='gargantua').first())

    try:
        moissonneur.query(request)
        corpus = moissonneur.save(request, project.id, return_corpus=True)

    except (ValueError, Http404) as e:
        raise e

    # Sometimes strange things happens...
    if corpus.name != name:
        corpus.name = name
        session.commit()

    return corpus
