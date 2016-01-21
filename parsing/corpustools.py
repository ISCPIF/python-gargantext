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

from re import sub

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
def add_resource(corpus, mysession=None, **kwargs):
    
    if mysession is None:
        from gargantext_web.db import session
        mysession = session
    
    # only for tests
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
    tmp_resource = (mysession
        .query(Resource)
        .join(Node_Resource, Node_Resource.resource_id == Resource.id)
        .filter(Resource.digest == resource.digest)
        .filter(Node_Resource.node_id == corpus.id)
    ).first()
    if tmp_resource is not None:
        return tmp_resource
    else:
        mysession.add(resource)
        mysession.commit()
    # link with the resource
    node_resource = Node_Resource(
        node_id = corpus.id,
        resource_id = resource.id,
        parsed = False,
    )
    mysession.add(node_resource)
    mysession.commit()
    return resource
    

def parse_resources(corpus, user=None, user_id=None, mysession=None):
    
    if mysession is None:
        from gargantext_web.db import session
        mysession = session
    
    dbg = DebugTime('Corpus #%d - parsing' % corpus.id)

    corpus_id = corpus.id
    type_id = cache.NodeType['Document'].id
    if user_id is None and user is not None:
        user_id = user.id
    else:
        user_id = corpus.user_id
    # find resource of the corpus
    resources_query = (mysession
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
    mysession.add_all(nodes)
    mysession.commit()
    # now, index the hyperdata
    dbg.show('insert hyperdata')
    node_hyperdata_lists = defaultdict(list)
    hyperdata_types = {
        hyperdata.name: hyperdata
        for hyperdata in mysession.query(Hyperdata)
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
        hyperdata_set.add(mysession.query(Hyperdata.id).filter(Hyperdata.name==field).first()[0])
    
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

def extract_ngrams(corpus, keys, nlp=True, mysession=None):
    
    if mysession is None:
        from gargantext_web.db import session
        mysession = session
    
    dbg = DebugTime('Corpus #%d - ngrams' % corpus.id)
    default_language_iso2 = None if corpus.language_id is None else cache.Language[corpus.language_id].iso2
    # query the hyperdata associated with the given keys
    columns = [Node.id, Node.language_id] + [Node.hyperdata[key] for key in keys]
    hyperdata_query = (mysession
        .query(*columns)
        .filter(Node.parent_id == corpus.id)
        .filter(Node.type_id == cache.NodeType['Document'].id)
    )
    # prepare data to be inserted
    dbg.show('find ngrams')
    languages_by_id = {
        language.id: language.iso2
        for language in mysession.query(Language)
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
                # normalisation caras (harmonisation guillemets etc)
                clean_text = text_prepa(text).lower()
                
                # TOTEST sent_tokenize (with nltk models) => [sentences]
                # then: for sentence => ngramsextract => ngrams.append()
                
                # TOTEST " ".join(wordpunct_tokenize(text)) pour éviter:
                #   - "vvsp+vvmi/vvmf"
                #   - "-stimulated increase"
                
                if nlp == True:
                    ngrams = ngramsextractor.extract_ngrams(clean_text)
                else:
                    ngrams = wordpunct_tokenize(clean_text)

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
    

def text_prepa(my_str):
    """
    Simplification des chaînes de caractères pour le tagging
       - suppression/normalisation espaces et ponctuations
       - jonction césures,
       - déligatures
       - tout en min
    
    (c) rloth 2010 - 2016
    """
    # --------------
    # E S P A C E S
    # --------------
    # tous les caractères de contrôle (dont \t = \x{0009}, \n = \x{000A} et \r = \x{000D}) --> espace
    my_str = sub(r'[\u0000\u0001\u0002\u0003\u0004\u0005\u0006\u0007\u0008\u0009\u000A\u000B\u000C\u000D\u000E\u000F\u0010\u0011\u0012\u0013\u0014\u0015\u0016\u0017\u0018\u0019\u001A\u001B\u001C\u001D\u001E\u001F\u007F]', ' ', my_str)
    
    # Line separator
    my_str = sub(r'\u2028',' ', my_str)
    my_str = sub(r'\u2029',' ', my_str)
    
    # U+0092: parfois quote parfois cara de contrôle
    my_str = sub(r'\u0092', ' ', my_str)   
    
    # tous les espaces alternatifs --> espace
    my_str = sub(r'[\u00A0\u1680\u180E\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200A\u200B\u202F\u205F\u3000\uFEFF]', ' ' , my_str)
    
    # pour finir on enlève les espaces en trop
    # (dits "trailing spaces")
    my_str = sub(r'\s+', ' ', my_str)
    my_str = sub(r'^\s', '', my_str)
    my_str = sub(r'\s$', '', my_str)
    
    
    # ------------------------
    # P O N C T U A T I O N S
    # ------------------------
    # la plupart des tirets alternatifs --> tiret normal (dit "du 6")
    # (dans l'ordre U+002D U+2010 U+2011 U+2012 U+2013 U+2014 U+2015 U+2212 U+FE63)
    my_str = sub(r'[‐‑‒–—―−﹣]','-', my_str)

    # le macron aussi parfois comme tiret
    # (mais compatibilité avec desaccent ?)
    my_str = sub(r'\u00af','-', my_str)

    # Guillemets
    # ----------
    # la plupart des quotes simples --> ' APOSTROPHE
    my_str = sub(r"‘’‚`‛", "'", my_str) # U+2018 U+2019 U+201a U+201b
    my_str = sub(r'‹ ?',"'", my_str)    # U+2039 plus espace éventuel après
    my_str = sub(r' ?›',"'", my_str)    # U+203A plus espace éventuel avant
    
    # la plupart des quotes doubles --> " QUOTATION MARK
    my_str = sub(r'“”„‟', '"', my_str)  # U+201C U+201D U+201E U+201F
    my_str = sub(r'« ?', '"', my_str)   # U+20AB plus espace éventuel après
    my_str = sub(r' ?»', '"', my_str)   # U+20AB plus espace éventuel avant
    
    # deux quotes simples (préparées ci-dessus) => une double
    my_str = sub(r"''", '"', my_str)
    
    # Autres
    # -------
    my_str = sub(r'…', '...', my_str)
    # paragraph separator utilisé parfois comme '...'
    my_str = sub(r'\u0085', '...', my_str)
    my_str = sub(r'€', 'EUR', my_str)
    
    # quelques puces courantes (bullets)
    my_str = sub(r'▪', '*', my_str)
    my_str = sub(r'►', '*', my_str)
    my_str = sub(r'●', '*', my_str)
    my_str = sub(r'◘', '*', my_str)
    my_str = sub(r'→', '*', my_str)
    my_str = sub(r'•', '*', my_str)
    my_str = sub(r'·', '*', my_str)
    my_str = sub(r'☽', '*', my_str)
    
    # --------------
    # C E S U R E S
    # --------------
    # NB: pré-suppose déjà: tr '\n' ' ' et normalisation des tirets
    my_str = sub(r'(?<=\w)- ', '-', my_str) # version light avec tiret préservé
    
    
    # ------------------
    # L I G A T U R E S
    # ------------------
    my_str = sub(r'Ꜳ', 'AA', my_str)
    my_str = sub(r'ꜳ', 'aa', my_str)
    my_str = sub(r'Æ', 'AE', my_str)
    my_str = sub(r'æ', 'ae', my_str)
    my_str = sub(r'Ǳ', 'DZ', my_str)
    my_str = sub(r'ǲ', 'Dz', my_str)
    my_str = sub(r'ǳ', 'dz', my_str)
    my_str = sub(r'ﬃ', 'ffi', my_str)
    my_str = sub(r'ﬀ', 'ff', my_str)
    my_str = sub(r'ﬁ', 'fi', my_str)
    my_str = sub(r'ﬄ', 'ffl', my_str)
    my_str = sub(r'ﬂ', 'fl', my_str)
    my_str = sub(r'ﬅ', 'ft', my_str)
    my_str = sub(r'Ĳ', 'IJ', my_str)
    my_str = sub(r'ĳ', 'ij', my_str)
    my_str = sub(r'Ǉ', 'LJ', my_str)
    my_str = sub(r'ǉ', 'lj', my_str)
    my_str = sub(r'Ǌ', 'NJ', my_str)
    my_str = sub(r'ǌ', 'nj', my_str)
    my_str = sub(r'Œ', 'OE', my_str)
    my_str = sub(r'œ', 'oe', my_str)
    my_str = sub(r'\u009C', 'oe', my_str)   # U+009C (cara contrôle vu comme oe)
    my_str = sub(r'ﬆ', 'st', my_str)
    my_str = sub(r'Ꜩ', 'Tz', my_str)
    my_str = sub(r'ꜩ', 'tz', my_str)
        
    return my_str
