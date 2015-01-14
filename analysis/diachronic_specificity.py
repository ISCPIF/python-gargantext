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


def diachronic_specificity(corpus_id, string, order=True):
    ''' 
    Take as parameter Corpus primary key and text of ngrams.
    Result is a dictionnary.
    Keys are period (years for now)
    Values are measure to indicate diachronic specificity.
    Nowadays, the measure is rather simple: distance of frequency of period from mean of frequency of all corpus.
    '''
    corpus = session.query(Node).get(int(corpus_id))
    ngram = session.query(Ngram).filter(Ngram.terms == string).first()
    
    ngram_frequency_query = session.query(Node.metadata['publication_year'], func.count('*'))                        .join(NodeNgram, Node.id == NodeNgram.node_id)                        .filter( NodeNgram.ngram == ngram)                        .filter(Node.parent_id == corpus.id)                        .group_by(Node.metadata['publication_year']).all()

    document_year_sum_query = session.query(Node.metadata['publication_year'], func.count('*'))            .filter(Node.parent_id == corpus.id)            .group_by(Node.metadata['publication_year']).all()
            
            
    document_filterByngram_year = result2dict(ngram_frequency_query)
    document_all_year = result2dict(document_year_sum_query)
    #print(document_all_year)
    data = dict()
    
    for year in document_all_year.keys():
       data[year] = document_filterByngram_year.get(year, 0) / document_all_year[year]
    
    mean = np.mean(list(data.values()))
    
    data_dict = dict(zip(data.keys(), list(map(lambda x: x - mean, data.values()))))
    
    if order == True:
        return collections.OrderedDict(sorted(data_dict.items()))
    else:
        return data_dict


# For tests
#diachronic_specificity(102750, "bayer", order=True)


