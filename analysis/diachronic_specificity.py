import sqlalchemy
from gargantext_web import api
from gargantext_web.db import *

from node import models
from sqlalchemy import create_engine
from sqlalchemy.sql import func
import numpy as np
import collections



def result2dict(query):
    results = dict()
    for result in query:
        if result[0] is not None:
            results[result[0]] = result[1]
    return(results)


def diachronic_specificity(corpus_id, terms, order=True):
    '''
    Take as parameter Corpus primary key and text of ngrams.
    Result is a dictionnary.
    Keys are period (years for now)
    Values are measure to indicate diachronic specificity.
    Nowadays, the measure is rather simple: distance of frequency of period from mean of frequency of all corpus.
    '''
    # implicit global session
    ngram_frequency_query = (session
        .query(Node.hyperdata['publication_year'], func.count('*'))
        .join(NodeNgram, Node.id == NodeNgram.node_id)
        .join(Ngram, Ngram.id == NodeNgram.ngram_id)
        .filter(Ngram.terms == terms)
        .filter(Node.parent_id == corpus_id)
        .group_by(Node.hyperdata['publication_year'])
    )

    document_year_sum_query = (session
        .query(Node.hyperdata['publication_year'], func.count('*'))
        .filter(Node.parent_id == corpus_id)
        .group_by(Node.hyperdata['publication_year'])
    )


    document_filterByngram_year = dict(ngram_frequency_query.all())
    document_all_year = dict(document_year_sum_query.all())
    #print(document_all_year)

    relative_terms_count = dict()
    for year, total in document_all_year.items():
        terms_count = document_filterByngram_year.get(year, 0)
        relative_terms_count[year] = terms_count / total

    mean = np.mean(list(relative_terms_count.values()))

    relative_terms_count = {
        key: (value - mean)
        for key, value in relative_terms_count.items()
    }

    if order == True:
        return collections.OrderedDict(sorted(relative_terms_count.items()))
    else:
        return relative_terms_count

# For tests
# diachronic_specificity(102750, "bayer", order=True)
# diachronic_specificity(26128, "bee", order=True)
