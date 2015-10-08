from collections import defaultdict
from datetime import datetime
from random import random
from hashlib import md5
from math import log

from admin.utils import DebugTime

from gargantext_web.db import *

from .parsers_config import parsers as _parsers


# keep all the parsers in a cache
class Parsers(defaultdict):
    def __init__(self):
        self._parsers = _parsers

    def __missing__(self, key):
        #print(self._parsers.keys())
        if key not in self._parsers.keys():
            raise NotImplementedError('No such parser: "%s"' % (key))
        parser = self._parsers[key]()
        self[key] = parser
        return parser

parsers = Parsers()


# resources management
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
    dbg = DebugTime('Corpus #%d - parsing' % corpus.id)
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
    # print(resources_query)
    dbg.show('analyze documents')
    nodes = list()
    for resource, resourcetype in resources_query:
        # print("resource: ",resource)
        # print("resourcetype:",resourcetype)
        # print(resourcetype.name)
        # print(resource.file)
        parser = parsers[resourcetype.name]
        # print(parser.parse(resource.file))
        for hyperdata_dict in parser.parse(resource.file):
            # retrieve language ID from hyperdata
            if 'language_iso2' in hyperdata_dict:
                try:
                    language_id = cache.Language[hyperdata_dict['language_iso2']].id
                except KeyError:
                    language_id = None
            else:
                language_id = None
            # create new node
            # print(hyperdata_dict.get('title', '')[:200])
            node = Node(
                name = hyperdata_dict.get('title', '')[:200],
                parent_id = corpus_id,
                user_id = user_id,
                type_id = type_id,
                language_id = language_id,
                hyperdata = hyperdata_dict,
                date = datetime.utcnow(),
            )
            nodes.append(node)
            #
            # TODO: mark node-resources associations as parsed
            #
    dbg.show('insert %d documents' % len(nodes))
    session.add_all(nodes)
    session.commit()
    # now, index the hyperdata
    dbg.show('insert hyperdata')
    node_hyperdata_lists = defaultdict(list)
    hyperdata_types = {
        hyperdata.name: hyperdata
        for hyperdata in session.query(Hyperdata)
    }
    #print('hyperdata_types', hyperdata_types)
    for node in nodes:
        node_id = node.id
        for hyperdata_key, hyperdata_value in node.hyperdata.items():
            try:
                hyperdata = hyperdata_types[hyperdata_key]
            except KeyError:
                continue
            if hyperdata.type == 'string':
                hyperdata_value = hyperdata_value[:255]
            node_hyperdata_lists[hyperdata.type].append((
                node_id,
                hyperdata.id,
                hyperdata_value,
            ))

    #print('I am here', node_hyperdata_lists.items())

    for key, values in node_hyperdata_lists.items():
        #print('here', key, values)
        bulk_insert(Node_Hyperdata, ['node_id', 'hyperdata_id', 'value_'+key], values)
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
    dbg = DebugTime('Corpus #%d - ngrams' % corpus.id)
    default_language_iso2 = None if corpus.language_id is None else cache.Language[corpus.language_id].iso2
    # query the hyperdata associated with the given keys
    columns = [Node.id, Node.language_id] + [Node.hyperdata[key] for key in keys]
    hyperdata_query = (session
        .query(*columns)
        .filter(Node.parent_id == corpus.id)
        .filter(Node.type_id == cache.NodeType['Document'].id)
    )
    # prepare data to be inserted
    dbg.show('find ngrams')
    languages_by_id = {
        language.id: language.iso2
        for language in session.query(Language)
    }

    ngrams_data = set()
    ngrams_language_data = set()
    ngrams_tag_data = set()

    node_ngram_list = defaultdict(lambda: defaultdict(int))
    for nodeinfo in hyperdata_query:
        node_id = nodeinfo[0]
        language_id = nodeinfo[1]

        if language_id is None:
            language_iso2 = default_language_iso2
        else:
            language_iso2 = languages_by_id.get(language_id, None)
        if language_iso2 is None:
            continue

        ngramsextractor = ngramsextractors[language_iso2]
        for text in nodeinfo[2:]:
            if text is not None and len(text):
                ngrams = ngramsextractor.extract_ngrams(text.replace("[","").replace("]",""))
                for ngram in ngrams:
                    n = len(ngram)
                    terms    = ' '.join([token for token, tag in ngram]).lower()
                    # TODO BUG here
                    if n == 1:
                        #tag_id   = cache.Tag[ngram[0][1]].id
                        tag_id   =  1
                        #print('tag_id', tag_id)
                    elif n > 1:
                        tag_id   =  1
                        #tag_id   = cache.Tag[ngram[0][1]].id
                        #tag_id   = cache.Tag['NN'].id
                        #tag_id   =  14
                        #print('tag_id_2', tag_id)
                    node_ngram_list[node_id][terms] += 1
                    ngrams_data.add((n, terms[:255]))
                    ngrams_language_data.add((terms, language_id))
                    ngrams_tag_data.add((terms, tag_id))

    # insert ngrams to temporary table
    dbg.show('find ids for the %d ngrams' % len(ngrams_data))
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
    dbg.show('insert associations')
    node_ngram_data = list()
    for node_id, ngrams in node_ngram_list.items():
        for terms, weight in ngrams.items():
            try:
                ngram_id = ngram_ids[terms]
                node_ngram_data.append((node_id, ngram_id, weight, ))
            except Exception as e:
                print("err01:",e)
    bulk_insert(Node_Ngram, ['node_id', 'ngram_id', 'weight'], node_ngram_data, cursor=cursor)
    dbg.message = 'insert %d associations' % len(node_ngram_data)
    # commit to database
    db.commit()





