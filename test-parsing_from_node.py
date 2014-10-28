from node.models import Node, NodeType, User, Language
from parsing.Caches import Cache

try:
    me = User.objects.get(username='Mat')
except:
    me = User(username='Mat')
    me.save()

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
    for i in range(64):
        title = 'Document #%d' % i
        Node(
            user        = me,
            # type        = self._document_nodetype,
            name        = title,
            language    = english,
            metadata    = {'title':title},
            #resource    = resource,
            type        = typeDoc,
            parent      = corpus
        ).save()

corpus.add_resource(file='/path/to/file')
corpus.parse()

exit()

cache = Cache()
for child in corpus.children.all():
    print(child.id)
    child.extract_ngrams(['title'], cache)