import sqlalchemy
from gargantext_web import api
from node import models
from sqlalchemy import create_engine
from sqlalchemy.sql import func
import numpy as np
import collections

NodeType = models.NodeType.sa
NodeNgram = models.Node_Ngram.sa
NodeNodeNgram = models.NodeNgramNgram.sa
Ngram = models.Ngram.sa
Node_Metadata = models.Node_Metadata.sa
Metadata = models.Metadata.sa
Node = models.Node.sa
Corpus = models.Corpus.sa

def get_session():
    import sqlalchemy.orm
    from django.db import connections
    from sqlalchemy.orm import sessionmaker
    from aldjemy.core import get_engine
    alias = 'default'
    connection = connections[alias]
    engine = create_engine("postgresql+psycopg2://alexandre:C8kdcUrAQy66U@localhost/gargandb",
            use_native_hstore=True)
    Session = sessionmaker(bind=engine)
    return Session()

session = get_session()


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
    ngram_frequency_query = (session
        .query(Node.metadata['publication_year'], func.count('*'))
        .join(NodeNgram, Node.id == NodeNgram.node_id)
        .join(Ngram, Ngram.id == NodeNgram.ngram_id)
        .filter(Ngram.terms == terms)
        .filter(Node.parent_id == corpus_id)
        .group_by(Node.metadata['publication_year'])
    )

    document_year_sum_query = (session
        .query(Node.metadata['publication_year'], func.count('*'))
        .filter(Node.parent_id == corpus_id)
        .group_by(Node.metadata['publication_year'])
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
