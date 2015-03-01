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



# resources managment

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
    print('PARSE RESOURCES: retrieve documents')
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
    print('PARSE RESOURCES: insert documents')
    session.add_all(nodes)
    session.commit()
    # now, index the metadata
    print('PARSE RESOURCES: insert metadata')
    node_metadata_lists = defaultdict(list)
    for node in nodes:
        node_id = node.id
        for metadata_key, metadata_value in node.metadata.items():
            try:
                metadata = cache.Metadata[metadata_key]
            except KeyError:
                continue
            if metadata.type == 'string':
                metadata_value = metadata_value[:255]
            node_metadata_lists[metadata.type].append((
                node_id,
                metadata.id,
                metadata_value,
            ))
    for key, values in node_metadata_lists.items():
        bulk_insert(Node_Metadata, ['node_id', 'metadata_id', 'value_'+key], values)
    # mark the corpus as parsed
    corpus.parsed = True


# ngrams extraction

from .NgramsExtractors import EnglishNgramsExtractor, FrenchNgramsExtractor, NgramsExtractor

class NgramsExtractors(defaultdict):

    def __init__(self):
        # English
        self['en'] = EnglishNgramsExtractor()
        for key in ('eng', 'english'):
            self[key] = self['en']
        # French
        self['fr'] = FrenchNgramsExtractor()
        for key in ('fre', 'french'):
            self[key] = self['fr']
        # default
        self['default'] = NgramsExtractor()

    def __missing__(self, key):
        formatted_key = key.strip().lower()
        if formatted_key in self:
            self[key] = self[formatted_key]
        else:
            self[key] = self['default']
            # raise NotImplementedError
        return self[key]

ngramsextractors = NgramsExtractors()

def extract_ngrams(corpus, keys):
    default_language_iso2 = None if corpus.language_id is None else cache.Language[corpus.language_id].iso2
    # query the metadata associated with the given keys
    columns = [Node.id, Node.language_id] + [Node.metadata[key] for key in keys]
    metadata_query = (session
        .query(*columns)
        .filter(Node.parent_id == corpus.id)
        .filter(Node.type_id == cache.NodeType['Document'].id)
    )
    # prepare data to be inserted
    print('EXTRACT NGRAMS: find ngrams')
    ngrams_data = set()
    node_ngram_list = defaultdict(lambda: defaultdict(int))
    for nodeinfo in metadata_query:
        node_id = nodeinfo[0]
        language_id = nodeinfo[1]
        language_iso2 = default_language_iso2 if language_id is None else cache.Language[language_id].iso2
        ngramsextractor = ngramsextractors[language_iso2]
        for text in nodeinfo[2:]:
            if text is not None:
                ngrams = ngramsextractor.extract_ngrams(text)
                for ngram in ngrams:
                    terms = ' '.join([token for token, tag in ngram]).lower()
                    n = len(ngram)
                    node_ngram_list[node_id][terms] += 1
                    ngrams_data.add(
                        (n, terms)
                    )
    # insert ngrams to temporary table
    print('EXTRACT NGRAMS: find ngrams ids')
    db, cursor = get_cursor()
    cursor.execute('''
        CREATE TEMPORARY TABLE tmp__ngrams (
            id INT,
            n INT NOT NULL,
            terms VARCHAR(255) NOT NULL
        )
    ''')
    bulk_insert('tmp__ngrams', ['n', 'terms'], ngrams_data, cursor=cursor)
    # retrieve ngram ids from already inserted stuff
    cursor.execute('''
        UPDATE
            tmp__ngrams
        SET
            id = ngram.id
        FROM
            %s AS ngram
        WHERE
            ngram.terms = tmp__ngrams.terms
    ''' % (Ngram.__table__.name, ))
    # insert, then get the ids back
    cursor.execute('''
        INSERT INTO
            %s (n, terms)
        SELECT
            n, terms
        FROM
            tmp__ngrams
        WHERE
            id IS NULL
    ''' % (Ngram.__table__.name, ))
    cursor.execute('''
        UPDATE
            tmp__ngrams
        SET
            id = ngram.id
        FROM
            %s AS ngram
        WHERE
            ngram.terms = tmp__ngrams.terms
        AND
            tmp__ngrams.id IS NULL
    ''' % (Ngram.__table__.name, ))
    # get all ids
    ngram_ids = dict()
    cursor.execute('SELECT id, terms FROM tmp__ngrams')
    for row in cursor.fetchall():
        ngram_ids[row[1]] = row[0]
    # 
    print('EXTRACT NGRAMS: insert associations')
    node_ngram_data = list()
    for node_id, ngrams in node_ngram_list.items():
        for terms, weight in ngrams.items():
            ngram_id = ngram_ids[terms]
            node_ngram_data.append((node_id, ngram_id, weight, ))
    bulk_insert(Node_Ngram, ['node_id', 'ngram_id', 'weight'], node_ngram_data, cursor=cursor)
    # commit to database
    db.commit()
