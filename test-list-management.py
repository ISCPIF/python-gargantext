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

doc_id = session.query(Node.id).filter(Node.parent_id == corpus.id,
                                       Node.type_id   == cache.NodeType['Document'].id).all()[1]

print('Miam list', listIds(typeList='MiamList', corpus_id=corpus.id, user_id=user.id)[0][0])

# Stemming the corpus
print('Working on corpus:', corpus.id, corpus.name)
stem_id = stem_corpus(corpus_id=corpus.id)
print('Stem Node.id is', stem_id)

for typeList in ['MiamList', 'StopList', 'MainList', 'Group']:
    n = listIds(user_id=user.id,
                           corpus_id=corpus.id,
                           typeList=typeList)
    #print(n[0][0])
    print('Test having list_id')
    print(n, listNgramIds(list_id=n[0][0])[:3])


stop_list_id = listIds(user_id=user.id,
                       corpus_id=corpus.id,
                       typeList='StopList')[0][0]

miam_list_id = listIds(user_id=user.id,
                       corpus_id=corpus.id,
                       typeList='MiamList')[0][0]


print('Stop List', stop_list_id)
print('Miam List', miam_list_id)

ngram_id = listNgramIds(list_id=miam_list_id)[0][0]
print('ngram_id', ngram_id)

ngramList(do='add', ngram_ids=[ngram_id,], list_id=stop_list_id)





#
#    print('Test having typeList and corpus.id')
#    print(n, listNgramIds(typeList=typeList, corpus_id=corpus.id, user_id=user.id)[:3])
##
#    print('Test having typeList and corpus.id and doc_id')
#    print(n, listNgramIds(typeList=typeList, corpus_id=corpus.id, doc_id=doc_id, user_id=user.id)[:3])

#
#
#type_list='miam'
#try:
#    d = doList(type_list=type_list, user_id = user.id, corpus_id = corpus.id, stem_id=stem_id, limit=150)
#    print('Size of the ' + type_list + ' list:',
#          session.query(NodeNgram).filter(NodeNgram.node_id == d).count()
#          )
#except:
#    PrintException()
#
