# Without this, we couldn't use the Django environment
from admin.env import *

from ngram.stemLem import *
from ngram.lists import *

#from cooccurrences import *

#from gargantext_web.views import empty_trash
#empty_trash()
#

#user = session.query(User).all()[0]
user = session.query(User).filter(User.username=='alexandre').first()
print('Current user is:', user.username)

project = session.query(Node).filter(Node.name == 'Test').first()

if project is None:
    project = Node(
        name = 'Test',
        type_id = cache.NodeType['Project'].id,
        user_id = user.id
    )

    session.add(project)
    session.commit()

#corpora = session.query(Node).filter(Node.parent_id == project.id,
#                           Node.type_id == cache.NodeType['Corpus'].id
#                           ).delete()
#
#models.Node.objects(parent_id = project.id, type_id = cache.NodeType['Corpus']).all().delete()
#

corpus = session.query(Node).filter(Node.parent_id == project.id,
                                    Node.type_id   == cache.NodeType['Corpus'].id).first()

if corpus is None:
    corpus = Node(
        parent_id = project.id,
        name = 'Test Corpus',
        type_id = cache.NodeType['Corpus'].id,
        user_id = user.id
    )

    session.add(corpus)
    session.commit()

    add_resource(corpus,
        file = '/srv/gargantext_lib/data_samples/pubmed.zip',
#    #file = '/srv/gargantext_lib/data_samples/pubmed_2013-04-01_HoneyBeesBeeBees.xml',
        type_id = cache.ResourceType['Pubmed (xml format)'].id,
    )
    parse_resources(corpus)
    extract_ngrams(corpus, ('title', 'abstract'))
    compute_tfidf(corpus)



# Stemming the corpus
print('Working on corpus:', corpus.id, corpus.name)
stem_id = stem_corpus(corpus_id=corpus.id)
print('Stem Node.id is', stem_id)

for typeList in ['MiamList', 'StopList', 'MainList', 'Stem']:
    n = nodeList(user_id=user.id,
                           corpus_id=corpus.id,
                           typeList=typeList)
    print(n)


type_list='miam'
try:
    d = doList(type_list=type_list, user_id = user.id, corpus_id = corpus.id, stem_id=stem_id, limit=150)
    print('Size of the ' + type_list + ' list:',
          session.query(NodeNgram).filter(NodeNgram.node_id == d).count()
          )
except:
    PrintException()

