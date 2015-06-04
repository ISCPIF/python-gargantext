
from env import *
from gargantext_web.db import *
from parsing.corpustools import *

from gargantext_web.views import move_to_trash, empty_trash

def do_empty():
    corpus_ids = (session.query(Node.id)
            .filter(Node.type_id == cache.NodeType['Corpus'].id)
            .all()
            )

    for corpus_id in corpus_ids :
        doc_count = int()
        doc_count = (session.query(Node.id)
                .filter(Node.parent_id == corpus_id)
                .filter(Node.type_id == cache.NodeType['Document'].id)
                .count()
                )
        if doc_count == 0 :
            move_to_trash(corpus_id)

    empty_trash()

do_empty()


def extract_again():
    corpus_ids = (session.query(Node.id)
            .join(Node_Resource, Node_Resource.node_id == Node.id)
            .join(Resource, Node_Resource.resource_id == Resource.id )
            .join(or_(Resource.name == 'Europress (French)',
                      Resource.name == 'Europress (English)'))
            .filter(Node.type_id == cache.NodeType['Corpus'].id )
            .filter(Node.resource_id == cache.NodeType['Corpus'].id)
            .all()
            )
    print(corpus_ids)

extract_again()

#add_resource(corpus,
#    # file = './data_samples/pubmed_result.xml',
#    file = '/srv/gargantext_lib/data_samples/pubmed_2013-04-01_HoneyBeesBeeBees.xml',
#    type_id = cache.ResourceType['pubmed'].id,
#)
#parse_resources(corpus)
#extract_ngrams(corpus, ('title', ))
#
#
#
## print(corpus)
## corpus = session.query(Node).filter(Node.id == 72771).first()
## corpus = session.query(Node).filter(Node.id == 73017).first()
# compute_tfidf(corpus)
