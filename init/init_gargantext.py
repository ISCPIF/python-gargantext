# Without this, we couldn't use the Django environment

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gargantext_web.settings")
os.environ.setdefault("DJANGO_HSTORE_GLOBAL_REGISTER", "False")

# We're gonna use all the models!

# Django models
from node import models

# SQLA models
from gargantext_web.db import *

# Reset: all data
#
#tables_to_empty = [
#    Node,
#    Node_Metadata,
#    Metadata,
#    NodeType,
#    ResourceType,
#    Resource,
#]
#for table in tables_to_empty:
#    print('Empty table "%s"...' % (table._meta.db_table, ))
#    table.objects.all().delete()


# Integration: metadata types

print('Initialize metadata...')
metadata = {
    'publication_date': 'datetime',
    'authors': 'string',
    'language_fullname': 'string',
    'abstract': 'text',
    'title': 'string',
    'source': 'string',
    'volume': 'string',
    'text': 'text',
    'page': 'string',
    'doi': 'string',
    'journal': 'string',
}
for name, type in metadata.items():
    models.Metadata(name=name, type=type).save()


# Integration: languages

print('Initialize languages...')
import pycountry
Language.objects.all().delete()
for language in pycountry.languages:
    if 'alpha2' in language.__dict__:
        Language(
            iso2 = language.alpha2,
            iso3 = language.bibliographic,
            fullname = language.name,
            implemented = 1 if language.alpha2 in ['en', 'fr'] else 0,
        ).save()

english = Language.objects.get(iso2='en')
french  = Language.objects.get(iso2='fr')


# Integration: users

print('Initialize users...')
me = models.User.objects.get_or_create(username='alexandre')
gargantua = models.User.objects.get_or_create(username='gargantua')
node_root = Node(user_id=gargantua.id, type_id=cache.NodeType['Root'].id, name='Root')
node_stem = Node(user_id=gargantua.id, type_id=cache.NodeType['Stem'].id, name='Stem', parent_id=node_root.id)
node_lem = Node(user_id=gargantua.id, type_id=cache.NodeType['Lem'].id, name='Lem', parent_id=node_root.id)

session.add(node_root)
session.add(node_stem)
session.add(node_lem)
session.commit()

# Integration: node types

print('Initialize node types...')

node_types = [
        'Root', 'Trash',
        'Project', 'Corpus', 'Document', 
        'Stem', 'Lem', 'Tfidf', 
        'Synonym', 
        'MiamList', 'StopList',
        'Cooccurrence', 'WhiteList', 'BlackList'
        ]

for node_type in node_types:
    models.NodeType.objects.get_or_create(name=node_type)

# Integration: resource types

print('Initialize resource...')

from parsing.parsers_config import parsers

for parser in parsers.keys():
    models.ResourceType.objects.get_or_create(name=parser)



# TODO 
# here some tests
# add a new project and some corpora to test it


# Integration: project
#
#print('Initialize project...')
#try:
#    project = Node.objects.get(name='Bees project')
#except:
#    project = Node(name='Bees project', type=typeProject, user=me)
#    project.save()
#

# Integration: corpus

#print('Initialize corpus...')
#try:
#    corpus_pubmed = Node.objects.get(name='PubMed corpus')
#except:
#    corpus_pubmed = Node(parent=project, name='PubMed corpus', type=typeCorpus, user=me)
#    corpus_pubmed.save()
#
#print('Initialize resource...')
#corpus_pubmed.add_resource(
#    # file='./data_samples/pubmed.zip',
#    #file='./data_samples/pubmed_2013-04-01_HoneyBeesBeeBees.xml',
#    file='/srv/gargantext_lib/data_samples/pubmed.xml',
#    type=typePubmed,
#    user=me
#)
#
#for resource in corpus_pubmed.get_resources():
#    print('Resource #%d - %s - %s' % (resource.id, resource.digest, resource.file))
#    
## print('Parse corpus #%d...' % (corpus_pubmed.id, ))
# corpus_pubmed.parse_resources(verbose=True)
# print('Extract corpus #%d...' % (corpus_pubmed.id, ))
# corpus_pubmed.children.all().extract_ngrams(['title',])
# print('Parsed corpus #%d.' % (corpus_pubmed.id, ))





# Instantiante table NgramTag:
f = open("part_of_speech_labels.txt", 'r')

for line in f.readlines():
    name, description = line.strip().split('\t')
    _tag = Tag(name=name, description=description)
    session.add(_tag)
session.commit()

f.close()


exit()
