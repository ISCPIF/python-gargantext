from collections import defaultdict

from gargantext_web.db import *

from .FileParsers import *


_parsers = {
    'pubmed'            : PubmedFileParser,
    'isi'               : IsiFileParser,
    'ris'               : RisFileParser,
    'europress'         : EuropressFileParser,
    'europress_french'  : EuropressFileParser,
    'europress_english' : EuropressFileParser,
}


def parse_corpus_resources(corpus, user=None, user_id=None):
    session = Session()
    type_id = cache.NodeType['Document']
    if user_id is None and user is not None:
        user_id = user.id
    # keep all the parsers in a cache
    parsers = defaultdict(lambda key: _parsers[key]())
    # find resource of the corpus
    resources_query = (session
        .query(Resource, ResourceType)
        .join(ResourceType, ResourceType.id == Resource.type_id)
        .join(Node_Resource, Node_Resource.resource_id == Resource)
        .join(Node, Node.id == Node_Resource.node_id)
        .filter(Node.parent_id == corpus.id)
    )
    # make a new node for every parsed document of the corpus
    nodes = list()
    for resource, resourcetype in resources_query:
        parser = parsers[resourcetype.name]
        for metadata_dict in resource:
            # retrieve language ID from metadata
            if 'language_iso2' in metadata_dict:
                try:
                    language_id = cache.Langage[metadata_dict['language_iso2']]
                except KeyError:
                    language_id = None
            else:
                language_id = None
            # create new node
            node = Node( 
                name = metadata.get('title', ''),
                parent_id = corpus.id,
                user_id = user_id,
                type_id = type_id,
                language_id = language_id,
                metadata = metadata_dict,
            )
            nodes.append(node)
    session.add_bulk(nodes)
    session.commit()
    # now, index the metadata
    for node in nodes:
        node_id = node.id
        for metadata_key, metadata_value in node.metadata.items():
            metadata = cache.Metadata[key]
            if metadata.type == 'string':
                metadata_value = metadata_value[:255]
                node_metadata = Node_Metadata(**{
                    'node_id': node_id,
                    'metadata_id': metadata.id,
                    'value_'+metadata.type: value,
                })
                session.add(node_metadata)
    session.commit()
    # mark the corpus as parsed
    corpus.parsed = True


def parse_corpus(corpus):
    # prepare the cache for ngrams
    from nodes import models
    ngrams = ModelCache(models.Node)
    # 
