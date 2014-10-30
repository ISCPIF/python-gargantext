from node.models import Node, NodeType, User, Language, ResourceType
from parsing.Caches import Caches

try:
    me = User.objects.get(username='Mat')
except:
    me = User(username='Mat')
    me.save()

try:
    typePubmed = ResourceType.get(name='pubmed')
except:
    typePubmed = ResourceType(name='pubmed')
    typePubmed.save()

try:
    typeCorpus = NodeType.get(name='corpus')
    typeDoc = NodeType.get(name='document')
except:
    typeCorpus = NodeType(name='corpus')
    typeCorpus.save()
    typeDoc = NodeType(name='document')
    typeDoc.save()

english = Language.objects.get(iso2='en')
    

Node.objects.all().delete()
try:
    corpus = Node.objects.get(name='My first corpus')
except:
    corpus = Node(name='My first corpus', type=typeCorpus, user=me)
    corpus.save()
    
print('Remove previously existing children of the corpus...')
corpus.children.all().delete()
print('Adding a resource to the corpus...')
corpus.add_resource(file='./data_samples/pubmed.zip', type=typePubmed)
print('Adding the corpus resources...')
corpus.parse_resources()
print('Extracting ngrams from the documents...')
corpus.children.all().extract_ngrams(['title', 'abstract'])
