from collections import defaultdict
from datetime import datetime
from random import random
from hashlib import md5
from math import log

from admin.utils import DebugTime

from gargantext_web.db import *
from gargantext_web.db import get_session

from .parsers_config import parsers as _parsers
from ngram.tools import insert_ngrams

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
    session = get_session()
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
    
    session = get_session()

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

    hyperdata_set = set()
    hyperdata_ngrams = set()
    node_hyperdata_ngrams = set()
    #for field in ['source', 'authors', 'journal']:
    for field in ['journal', 'authors']:
        hyperdata_set.add(session.query(Hyperdata.id).filter(Hyperdata.name==field).first()[0])
    
    #print("hyperdata_set", hyperdata_set)

    for key, values in node_hyperdata_lists.items():
        #print('here', key, values)
        bulk_insert(Node_Hyperdata, ['node_id', 'hyperdata_id', 'value_'+key], values)
        if key == 'string' :
            for value in values:
                if value[1] in hyperdata_set:
                    for val in value[2].split(', '):
                        hyperdata_ngrams.add((val, len(val.split(' '))))
                        node_hyperdata_ngrams.add((value[0], value[1], val))
    
    #print(hyperdata_ngrams)
    terms_id = insert_ngrams(list(hyperdata_ngrams))
    
    bulk_insert(NodeHyperdataNgram
               , ['node_id', 'hyperdata_id', 'ngram_id', 'score']
               , [(node_id, hyperdata_id, terms_id[terms], 1) 
                   for node_id, hyperdata_id, terms in list(node_hyperdata_ngrams)])

    # mark the corpus as parsed
    corpus.parsed = True


# ngrams extraction
from .NgramsExtractors import EnglishNgramsExtractor, FrenchNgramsExtractor, NgramsExtractor
from nltk.tokenize import word_tokenize, wordpunct_tokenize, sent_tokenize

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

def extract_ngrams(corpus, keys, nlp=True):
    dbg = DebugTime('Corpus #%d - ngrams' % corpus.id)
    session = get_session()
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
    #ngrams_tag_data = set()

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
                if nlp == True:
                    ngrams = ngramsextractor.extract_ngrams(text.replace("[","").replace("]",""))
                else:
                    ngrams = wordpunct_tokenize(text.lower())

                for ngram in ngrams:
                    if nlp == True:
                        n = len(ngram)
                        terms    = ' '.join([token for token, tag in ngram]).lower()
                    else:
                        terms = ngram
                        n = 1
                    # TODO BUG here
                    #if n == 1:
                        #tag_id   = cache.Tag[ngram[0][1]].id
                    #    tag_id   =  1
                        #print('tag_id', tag_id)
                    #elif n > 1:
                    #    tag_id   =  1
                        #tag_id   = cache.Tag[ngram[0][1]].id
                        #tag_id   = cache.Tag['NN'].id
                        #tag_id   =  14
                        #print('tag_id_2', tag_id)
                    node_ngram_list[node_id][terms] += 1
                    ngrams_data.add((terms[:255],n))
                    ngrams_language_data.add((terms, language_id))
                    #ngrams_tag_data.add((terms, tag_id))

    # insert ngrams to temporary table
    dbg.show('find ids for the %d ngrams' % len(ngrams_data))
    db, cursor = get_cursor()
    ngram_ids = insert_ngrams(ngrams_data)

    dbg.show('insert associations')
    node_ngram_data = set()
    for node_id, ngrams in node_ngram_list.items():
        for terms, weight in ngrams.items():
            try:
                ngram_id = ngram_ids[terms]
                node_ngram_data.add((node_id, ngram_id, weight, ))
            except Exception as e:
                print("err01:",e)
    bulk_insert(Node_Ngram, ['node_id', 'ngram_id', 'weight'], node_ngram_data, cursor=cursor)
    dbg.message = 'insert %d associations' % len(node_ngram_data)
    # commit to database
    db.commit()

