#
from admin.env import *
from admin.utils import PrintException
#from gargantext_web.settings import
#
#
## Django models
##from node import models
#
## SQLA models
from gargantext_web.db import session

################################################################################
## If you need to reset all data
## use : ./manage.py flush
################################################################################

################################################################################
print('Initialize hyperdata...')
################################################################################
hyperdata = {
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

for name_, type_ in hyperdata.items():
    data_      = (session.query(Hyperdata).filter(
                         Hyperdata.name == str(name_),
                         Hyperdata.type == str(type_)
                         ).first()
                 )
    if data_ is None:
        print('Hyper Data' + name_ + 'does not existe, creating it')
        hyperdata = Hyperdata(name=name_, type=type_)
        session.add(hyperdata)
session.commit()


## Integration: languages
##

################################################################################
print('Initialize languages...')
################################################################################
import pycountry
##Language.objects.all().delete()
for language in pycountry.languages:
    pass
    if 'alpha2' in language.__dict__:
        lang = Language(
        iso2 = language.alpha2,
        iso3 = language.bibliographic,
        fullname = language.name,
        implemented = True if language.alpha2 in ['en', 'fr'] else False
        )
        l = session.query(Language).filter(Language.iso2 == lang.iso2).first()
        if l is None:
            session.add(lang)
session.commit()


################################################################################
print('Initialize users...')
################################################################################
gargantua = session.query(User).filter(User.username=='gargantua').first()
if gargantua is None:
    from node.models import User as U
    gargantua = U()
    gargantua.username = 'gargantua'
    # Read specific email address here:
    gargantua.email     = 'contact@gargantext.org'
    gargantua.active_user = True
    password = U.objects.make_random_password()
    print('Gargantua, password: ', password)
    gargantua.set_password(password)
    gargantua.save()


################################################################################
print('Initialize node types...')
################################################################################
node_types = [
        'Root', 'Trash',
        'Project', 'Corpus', 'Document',
        'MiamList', 'StopList', 'MainList',
        'Stem', 'Lem', 'Group', 'Tfidf', 'Tfidf (global)',
        'Cooccurrence',
        ]

for node_type in node_types:
    nt = NodeType(name=node_type)
    if session.query(NodeType).filter(NodeType.name==nt.name).first() is None:
        session.add(nt)
session.commit()


################################################################################
print('Initialize main nodes...')
################################################################################
nodes = []
node_root = Node(user_id=gargantua.id, type_id=cache.NodeType['Root'].id, name='Root')
nodes.append(node_root)

node_stem = Node(user_id=gargantua.id, type_id=cache.NodeType['Stem'].id, name='Stem', parent_id=node_root.id)
nodes.append(node_stem)

node_lem = Node(user_id=gargantua.id, type_id=cache.NodeType['Lem'].id, name='Lem', parent_id=node_root.id)
nodes.append(node_lem)

for node in nodes:
    if session.query(Node).filter(Node.name==node.name, Node.user_id==node.user_id).first() is None:
        session.add(node)

session.commit()



################################################################################
print('Initialize resource...')
################################################################################

from parsing.parsers_config import parsers

for parser in parsers.keys():
    resource = ResourceType(name=parser)
    if session.query(ResourceType).filter(ResourceType.name==resource.name).first() is None:
        session.add(resource)

session.commit()

################################################################################
#### Instantiante table NgramTag:
################################################################################
###f = open("part_of_speech_labels.txt", 'r')
###
###for line in f.readlines():
###    name, description = line.strip().split('\t')
###    _tag = Tag(name=name, description=description)
###    session.add(_tag)
###session.commit()
###
###f.close()
##
##
#exit()
