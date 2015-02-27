from collections import defaultdict
from datetime import datetime

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



def parse_resources(corpus, user=None, user_id=None):
    session = Session()
    corpus_id = corpus.id
    type_id = cache.NodeType['Document'].id
    if user_id is None and user is not None:
        user_id = user.id
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
            node = Node()
            node.name = metadata_dict.get('title', '')
            node.parent_id = corpus_id
            node.user_id = user_id
            node.type_id = type_id
            node.language_id = language_id
            node.metadata = metadata_dict
            node.date = datetime.utcnow()
            nodes.append(node)
            #
            # TODO: mark node-resources associations as parsed
            # 
    session.add_all(nodes)
    session.commit()
    # now, index the metadata
    for node in nodes:
        node_id = node.id
        for metadata_key, metadata_value in node.metadata.items():
            metadata = cache.Metadata[key]
            if metadata.type == 'string':
                metadata_value = metadata_value[:255]
                node_metadata = Node_Metadata()
                node_metadata.node_id = node_id
                node_metadata.metadata_id = metadata.id
                setattr(node_metadata, 'value_'+metadata.type, metadata_value)
                session.add(node_metadata)
    session.commit()
    # mark the corpus as parsed
    corpus.parsed = True


def extract_ngrams(corpus):
    # prepare the cache for ngrams
    from nodes import models
    ngrams = ModelCache(models.Node)
    # 
