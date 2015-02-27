from collections import defaultdict
from datetime import datetime
from random import random
from hashlib import md5

from gargantext_web.db import *

from .FileParsers import *



# keep all the parsers in a cache
class Parsers(defaultdict):

    _parsers = {
        'pubmed'            : PubmedFileParser,
        'isi'               : IsiFileParser,
        'ris'               : RisFileParser,
        'europress'         : EuropressFileParser,
        'europress_french'  : EuropressFileParser,
        'europress_english' : EuropressFileParser,
    }

    def __missing__(self, key):
        if key not in self._parsers:
            raise NotImplementedError('No such parser: "%s"' % (key))
        parser = self._parsers[key]()
        self[key] = parser
        return parser

parsers = Parsers()



def add_resource(corpus, **kwargs):
    # only for tests
    session = Session()
    resource = Resource(guid=str(random()), **kwargs )
    # User
    if 'user_id' not in kwargs:
        resource.user_id = corpus.user_id
    # Compute the digest
    h = md5()
    f = open(str(resource.file), 'rb')
    h.update(f.read())
    f.close()
    resource.digest = h.hexdigest()
    # check if a resource on this node already has this hash
    tmp_resource = (session
        .query(Resource)
        .join(Node_Resource, Node_Resource.resource_id == Resource.id)
        .filter(Resource.digest == resource.digest)
        .filter(Node_Resource.node_id == corpus.id)
    ).first()
    if tmp_resource is not None:
        return tmp_resource
    else:
        session.add(resource)
        session.commit()
    # link with the resource
    node_resource = Node_Resource(
        node_id = corpus.id,
        resource_id = resource.id,
        parsed = False,
    )
    session.add(node_resource)
    session.commit()
    # return result
    return resource


def parse_resources(corpus, user=None, user_id=None):
    session = Session()
    corpus_id = corpus.id
    type_id = cache.NodeType['Document'].id
    if user_id is None and user is not None:
        user_id = user.id
    else:
        user_id = corpus.user_id
    # find resource of the corpus
    resources_query = (session
        .query(Resource, ResourceType)
        .join(ResourceType, ResourceType.id == Resource.type_id)
        .join(Node_Resource, Node_Resource.resource_id == Resource.id)
        .filter(Node_Resource.node_id == corpus.id)
        .filter(Node_Resource.parsed == False)
    )
    # make a new node for every parsed document of the corpus
    nodes = list()
    for resource, resourcetype in resources_query:
        parser = parsers[resourcetype.name]
        for metadata_dict in parser.parse(resource.file):
            # retrieve language ID from metadata
            if 'language_iso2' in metadata_dict:
                try:
                    language_id = cache.Language[metadata_dict['language_iso2']].id
                except KeyError:
                    language_id = None
            else:
                language_id = None
            # create new node
            node = Node(
                name = metadata_dict.get('title', ''),
                parent_id = corpus_id,
                user_id = user_id,
                type_id = type_id,
                language_id = language_id,
                metadata = metadata_dict,
                date = datetime.utcnow(),
            )
            nodes.append(node)
            #
            # TODO: mark node-resources associations as parsed
            # 
    session.add_all(nodes)
    session.commit()
    # now, index the metadata
    node_metadata_list = []
    for node in nodes:
        node_id = node.id
        for metadata_key, metadata_value in node.metadata.items():
            try:
                metadata = cache.Metadata[metadata_key]
            except KeyError:
                continue
            if metadata.type == 'string':
                metadata_value = metadata_value[:255]
            node_metadata_list.append({
                'node_id': node_id,
                'metadata_id': metadata.id,
                'value_'+metadata.type: metadata_value,
            })
    bulk_insert(Node_Metadata, node_metadata_list)
    # mark the corpus as parsed
    corpus.parsed = True


def extract_ngrams(corpus):
    # prepare the cache for ngrams
    from nodes import models
    ngrams = ModelCache(models.Node)
    # 
