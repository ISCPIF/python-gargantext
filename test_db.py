# Without this, we couldn't use the Django environment
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gargantext_web.settings")
os.environ.setdefault("DJANGO_HSTORE_GLOBAL_REGISTER", "False")

# database tools
from node import models
from gargantext_web.db import *
from parsing.corpustools import *




user = session.query(User).first()

project = session.query(Node).filter(Node.name == 'A').first()

corpus = Node(
    parent_id = project.id,
    name = 'Test 456',
    type_id = cache.NodeType['Corpus'].id,
    user_id = user.id,
)

session.add(corpus)
session.commit()

add_resource(corpus,
    # file = './data_samples/pubmed_result.xml',
    file = '/srv/gargantext_lib/data_samples/pubmed_2013-04-01_HoneyBeesBeeBees.xml',
    type_id = cache.ResourceType['pubmed'].id,
)
parse_resources(corpus)
extract_ngrams(corpus, ('title', ))



# print(corpus)
# corpus = session.query(Node).filter(Node.id == 72771).first()
# corpus = session.query(Node).filter(Node.id == 73017).first()
compute_tfidf(corpus)
