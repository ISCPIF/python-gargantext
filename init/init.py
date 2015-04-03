
# to be executed like this:
# ./manage.py shell < init.py



#NodeType.objects.all().delete()


from node.models import *


import pycountry

for language in pycountry.languages:
    try:
        implemented = 1 if language.alpha2 in ['en', 'fr'] else 0
        Language(iso2=language.alpha2, iso3=language.terminology, fullname=language.name, implemented=implemented).save()
    except:
        pass



english = Language.objects.get(iso2='en')
french  = Language.objects.get(iso2='fr')


try:
    me = User.objects.get(username='pksm3')
except:
    me = User(username='pksm3')
    me.save()

for node_type in ['Trash', 'Root', ]:
    NodeType.objects.get_or_create(name=node_type)

try:
    typeProject = NodeType.objects.get(name='Project')
except Exception as error:
    print(error)
    typeProject = NodeType(name='Project')
    typeProject.save()  

try:
    typeCorpus  = NodeType.objects.get(name='Corpus')
except Exception as error:
    print(error)
    typeCorpus  = NodeType(name='Corpus')
    typeCorpus.save()
    
try:
    typeDoc     = NodeType.objects.get(name='Document')
except Exception as error:
    print(error)
    typeDoc     = NodeType(name='Document')
    typeDoc.save()


try:
    typeStem     = NodeType.objects.get(name='Stem')
except Exception as error:
    print(error)
    typeStem     = NodeType(name='Stem')
    typeStem.save()

try:
    typeTfidf     = NodeType.objects.get(name='Tfidf')
except Exception as error:
    print(error)
    typeTfidf     = NodeType(name='Tfidf')
    typeTfidf.save()



try:
    typeDoc     = NodeType.objects.get(name='WhiteList')
except Exception as error:
    print(error)
    typeDoc     = NodeType(name='WhiteList')
    typeDoc.save()

try:
    typeDoc     = NodeType.objects.get(name='BlackList')
except Exception as error:
    print(error)
    typeDoc     = NodeType(name='BlackList')
    typeDoc.save()

try:
    typeDoc     = NodeType.objects.get(name='Synonyme')
except Exception as error:
    print(error)
    typeDoc     = NodeType(name='Synonyme')
    typeDoc.save()

try:
    typeDoc     = NodeType.objects.get(name='Cooccurrence')
except Exception as error:
    print(error)
    typeDoc     = NodeType(name='Cooccurrence')
    typeDoc.save()



# In[33]:

from parsing.parsers_config import parsers

ResourceType.objects.all().delete()

for key in parsers.keys():
    try:
        ResourceType.objects.get_or_create(name=key)
    except Exception as error:
        print("Ressource Error: ", error)


# In[34]:

#Node.objects.all().delete()




try:
    stem = Node.objects.get(name='Stem')
except:
    stem = Node(name='Stem', type=typeStem, user=me)
    stem.save()





from gargantext_web.db import *

# Instantiante table NgramTag:
f = open("part_of_speech_labels.txt", 'r')

for line in f.readlines():
    name, description = line.strip().split('\t')
    _tag = Tag(name=name, description=description)
    session.add(_tag)
session.commit()
f.close()


