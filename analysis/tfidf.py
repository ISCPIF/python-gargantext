
import sqlalchemy
from gargantext_web import api
from node import models
from sqlalchemy import create_engine
from sqlalchemy.sql import func
import numpy as np
import collections
from math import log
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
    engine = create_engine("postgresql+psycopg2://gargantua:C8kdcUrAQy66U@localhost/gargandb",
            use_native_hstore=True)
    Session = sessionmaker(bind=engine)
    return Session()

session = get_session()

type_doc = session.query(NodeType).filter(NodeType.name == "Document").first()

def tfidf(corpus, document, ngram):
    ''' 
    Compute TF-IDF (Term Frequency - Inverse Document Frequency)
    See: http://en.wikipedia.org/wiki/Tf%E2%80%93idf
    '''
    try:
        #occurences_of_ngram = Node_Ngram.objects.get(node=document, ngram=ngram).weight
        occurrences_of_ngram = session.query(NodeNgram)\
                .filter(NodeNgram.node_id == document.id)\
                .filter(NodeNgram.ngram_id == ngram.id)\
                .first().weight
        
        #return(type(occurrences_of_ngram))
        #ngrams_by_document = np.sum([ x.weight for x in Node_Ngram.objects.filter(node=document)])
        ngrams_by_document = session.query(NodeNgram).filter(NodeNgram.node_id == document.id).count()
        
        term_frequency = occurrences_of_ngram / ngrams_by_document
        #return term_frequency 
        
        #xx = Node.objects.filter(parent=corpus, type=NodeType.objects.get(name="Document")).count()
        xx = session.query(Node)\
                .filter(Node.parent_id == corpus.id)\
                .filter(Node.type_id   == type_doc.id)                .count()
        #yy = Node_Ngram.objects.filter(ngram=ngram).count() # filter: ON node.parent=corpus
        yy = session.query(NodeNgram)\
                .join(Node, NodeNgram.node_id == Node.id)\
                .filter(Node.parent_id == corpus.id)\
                .filter(NodeNgram.ngram_id == ngram.id)\
                .count()
        
        # print("\t\t\t","occs:",occurrences_of_ngram," || ngramsbydoc:",ngrams_by_document," || TF = occ/ngramsbydoc:",term_frequency," |||||| x:",xx," || y:",yy," || IDF = log(x/y):",log(xx/yy))
        inverse_document_frequency= log(xx/yy)

        # result = tf * idf
        result = term_frequency * inverse_document_frequency
 
        return result
    except Exception as error:
        print(error)


#corpus = session.query(Node).get(int(102750))
#ngram  = session.query(Ngram).get(10885)
##ngram = session.query(Ngram).filter(Ngram.terms == "bayer").first()
#type_doc = session.query(NodeType).filter(NodeType.name == "Document").first()
#doc_id  = session.query(NodeNgram.node, NodeNgram.node_id)\
#        .join(Node, Node.id == NodeNgram.node_id)\
#        .filter(NodeNgram.ngram == ngram)\
#        .filter(Node.type_id == type_doc.id)\
#        .first()
#document = session.query(Node).get(doc_id[1])
#
#result = tfidf(corpus,document, ngram)
#print(result)
#



