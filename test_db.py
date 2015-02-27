# Without this, we couldn't use the Django environment

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gargantext_web.settings")
os.environ.setdefault("DJANGO_HSTORE_GLOBAL_REGISTER", "False")




# perform a bulk insert, just to see

from gargantext_web.db import *

user = session.query(User).first()
project = session.query(Node).filter(Node.name == 'A').first()
corpus = Node(
    parent_id = project.id,
    name = 'Test 123',
    type_id = cache.NodeType['Corpus'].id,
    user_id = user.id,
)

session.add(corpus)
session.commit()

# 

from parsing.corpus import *

add_resource(corpus,
    file = './data_samples/pubmed_result.xml',
    type_id = cache.ResourceType['pubmed'].id,
)
parse_resources(corpus)
