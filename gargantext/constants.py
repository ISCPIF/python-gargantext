# WARNING: to ensure consistency and retrocompatibility, lists should keep the
#   initial order (ie., new elements should be appended at the end of the lists)
import importlib
from gargantext.util.lists import *
from gargantext.util.tools import datetime, convert_to_date
import re


# types & models (nodes, lists, hyperdata, resource) ---------------------------------------------
LISTTYPES = {
    'DOCUMENT'     : WeightedList,
    'GROUPLIST'    : Translations,   # todo remove "LIST" from name
    'STOPLIST'     : UnweightedList,
    'MAINLIST'     : UnweightedList,
    'MAPLIST'      : UnweightedList,
    'SPECCLUSION'  : WeightedList,
    'GENCLUSION'   : WeightedList,
    'OCCURRENCES'  : WeightedIndex,   # could be WeightedList
    'COOCCURRENCES': WeightedMatrix,
    'TFIDF-CORPUS' : WeightedIndex,
    'TFIDF-GLOBAL' : WeightedIndex,
    'TIRANK-LOCAL' : WeightedIndex,   # could be WeightedList
}
# 'OWNLIST'      : UnweightedList,    # £TODO use this for any term-level tags

NODETYPES = [
    # TODO separate id not array index, read by models.node
    None,                    # 0
    # documents hierarchy
    'USER',                  # 1
    'PROJECT',               # 2
    #RESOURCE should be here but last
    'CORPUS',                # 3
    'DOCUMENT',              # 4
    # lists
    'STOPLIST',              # 5
    'GROUPLIST',             # 6
    'MAINLIST',              # 7
    'MAPLIST',               # 8
    'COOCCURRENCES',         # 9
    # scores
    'OCCURRENCES',           # 10
    'SPECCLUSION',           # 11
    'CVALUE',                # 12
    'TFIDF-CORPUS',          # 13
    'TFIDF-GLOBAL',          # 14
    # docs subset
    'FAVORITES',             # 15
    # more scores (sorry!)
    'TIRANK-LOCAL',          # 16
    'TIRANK-GLOBAL',         # 17

    'GENCLUSION',            # 18
    'RESOURCE',              # 19
]

INDEXED_HYPERDATA = {
    # TODO use properties during toolchain.hyperdata_indexing
    # (type, convert_to_db, convert_from_db)

    'count':
        { 'id'             : 1
        , 'type'           : int
        , 'convert_to_db'  : int
        , 'convert_from_db': int
        },

    'publication_date':
        { 'id'             : 2
        , 'type'           : datetime.datetime
        , 'convert_to_db'  : convert_to_date
        , 'convert_from_db': datetime.datetime.fromtimestamp
        },

    'title':
        { 'id'             : 3
        , 'type'           : str
        , 'convert_to_db'  : str
        , 'convert_from_db': str
        },

    'authors':
        { 'id'             : 4
        , 'type'           : str
        , 'convert_to_db'  : str
        , 'convert_from_db': str
        },

    'journal':
        { 'id'             : 5
        , 'type'           : str
        , 'convert_to_db'  : str
        , 'convert_from_db': str
        },

    'abstract':
        { 'id'             : 6
        , 'type'           : str
        , 'convert_to_db'  : str
        , 'convert_from_db': str
        },

    # 'text':
    #     { 'id'             : 7
    #     , 'type'           : str
    #     , 'convert_to_db'  : str
    #     , 'convert_from_db': str
    #     },
    #
    # 'page':
    #     { 'id'             : 8
    #     , 'type'           : int
    #     , 'convert_to_db'  : int
    #     , 'convert_from_db': int
    #     },

}

# resources ---------------------------------------------
def get_resource(sourcetype):
    '''resource :: type => resource dict'''
    for n in RESOURCETYPES:
        if int(n["type"]) == int(sourcetype):
            return n
    return None
def get_resource_by_name(sourcename):
    '''resource :: name => resource dict'''
    for n in RESOURCETYPES:
        if str(n["name"]) == str(sourcename):
            return n
# taggers -----------------------------------------------
def get_tagger(lang):
    '''
    lang => default langage[0] => Tagger

    '''
    name = LANGUAGES[lang]["tagger"]
    module = "gargantext.util.taggers.%s" %(name)
    module = importlib.import_module(module, "")
    tagger = getattr(module, name)
    return tagger()




RESOURCETYPES = [
    {   "type":1,
        'name': 'Europress',
        'format': 'Europress',
        'parser': "EuropressParser",
        'file_formats':["zip"],
        'crawler': None,
        'default_languages': ['en', 'fr'],
    },
    {   'type': 2,
        'name': 'Jstor [RIS]',
        'format': 'RIS',
        'parser': "RISParser",
        'file_formats':["zip"],
        'crawler': None,
        'default_languages': ['en'],
    },
    {   'type': 3,
        'name': 'Pubmed [XML]',
        'format': 'Pubmed',
        'parser': "PubmedParser",
        'file_formats':["zip", "xml"],
        'crawler': "PubmedCrawler",
        'default_languages': ['en'],
    },
    {   'type':4,
        'name': 'Scopus [RIS]',
        'format': 'RIS',
        'parser': "RISParser",
        'file_formats':["zip"],
        'crawler': None,
        'default_languages': ['en'],
    },
    {   'type':5,
        'name': 'Web of Science [ISI]',
        'format': 'ISI',
        'parser': "ISIParser",
        'file_formats':["zip"],
        #'crawler': "ISICrawler",
        'crawler': None,
        'default_languages': ['en'],
    },
    {   'type':6,
        'name': 'Zotero [RIS]',
        'format': 'RIS',
        'parser': 'RISParser',
        'file_formats':["zip"],
        'crawler': None,
        'default_languages': ['en'],
    },
    {   'type':7,
        'name': 'CSV',
        'format': 'CSV',
        'parser': 'CSVParser',
        'file_formats':["zip", "csv"],
        'crawler': None,
        'default_languages': ['en'],
    },
    {   'type': 8,
        'name': 'ISTex [ISI]',
        'format': 'ISI',
        'parser': "ISTexParser",
        'file_formats':["zip"],
        #'crawler': "ISICrawler",
        'crawler': None,
        'default_languages': ['en', 'fr'],
    },
   {    "type":9,
        "name": 'SCOAP [XML]',
        "parser": "CernParser",
        "format": 'MARC21',
        'file_formats':["zip","xml"],
        "crawler": "CernCrawler",
        'default_languages': ['en'],
   },
]
#shortcut for resources declaration in template
PARSERS = [(n["type"],n["name"]) for n in RESOURCETYPES if n["parser"] is not None]
CRAWLERS = [(n["type"],n["name"]) for n in RESOURCETYPES if n["crawler"] is not None]

def load_parser(resource):
    '''given a resource load the corresponding Crawler
    resource(dict) > Parser(object)
    '''
    if resource["parser"] is not None:
        filename = resource["parser"].replace("Parser", '')
        print(filename)
        module = 'gargantext.util.parsers.%s' %(filename)
        module = importlib.import_module(module)
        return getattr(module, resource["parser"])
    else:
        return None

def load_crawler(resource):
    '''given a resource load the corresponding Parser()
    resource(dict) > Parser(object)
    '''
    filename = resource["name"].replace("Crawler", "")
    module = 'gargantext.util.crawlers.%s' %(filename)
    module = importlib.import_module(module)
    return getattr(module, resource.crawler)



# Supported languages and taggers ---------------------------------------------
#first declare the tagger using a string
#and it will be imported into gargantext.utils.taggers
LANGUAGES = {
    'en': {
        #'tagger': 'EnglishMeltTagger',
        #'tagger': "TurboTagger",
        'tagger': 'NltkTagger',
    },
    'fr': {
        #'tagger': "FrenchMeltTagger",
        #'tagger': 'TreeTagger',
        'tagger': 'NltkTagger',
    },
}

def load_tagger(lang):
    '''
    given a LANG load the corresponding tagger
    lang(str) > Tagger(Object)
    '''

    filename = LANGUAGES[lang]["tagger"]
    module = 'gargantext.util.taggers.%s' %(filename)
    module = importlib.import_module(module)
    return getattr(module, filename)


# linguistic extraction parameters ---------------------------------------------

DEFAULT_RANK_CUTOFF_RATIO      = .75         # MAINLIST maximum terms in %

DEFAULT_RANK_HARD_LIMIT        = 5000        # MAINLIST maximum terms abs
                                             # (makes COOCS larger ~ O(N²) /!\)

DEFAULT_COOC_THRESHOLD          = 3          # inclusive minimum for COOCS coefs
                                             # (makes COOCS more sparse)

DEFAULT_MAPLIST_MAX             = 350        # MAPLIST maximum terms

DEFAULT_MAPLIST_MONOGRAMS_RATIO = .2         # quota of monograms in MAPLIST
                                             # (vs multigrams = 1-mono)

DEFAULT_MAPLIST_GENCLUSION_RATIO = .6        # quota of top genclusion in MAPLIST
                                             # (vs top specclusion = 1-gen)

DEFAULT_MAX_NGRAM_LEN           = 7          # limit used after POStagging rule
                                             # (initial ngrams number is a power law of this /!\)
                                             # (and most longer ngrams have tiny freq anyway)

DEFAULT_ALL_LOWERCASE_FLAG      = True       # lowercase ngrams before recording
                                             # them to their DB table
                                             # (potentially bad for acronyms but
                                             #  good for variants like same term
                                             #  occurring at sentence beginning)

DEFAULT_INDEX_SUBGRAMS         = False        # False <=> traditional
                                             # True  <=>
                                             #  when ngram is like:
                                             #  "very cool example"
                                             #  then also count: "very", "cool"
                                             #  "example", "very cool" and
                                             #  "cool example".
                                             #   (all 1 to n-1 length ngrams,
                                             #    at indexing after extraction)
DEFAULT_INDEX_FIELDS            = ('title', 'abstract', ) #Defaults Fields for ngrams extraction
# Grammar rules for chunking
RULE_JJNN   = "{<JJ.*>*<NN.*|>+<JJ.*>*}"
RULE_JJDTNN = "{<JJ.*>*<NN.*>+((<P|IN> <DT>? <JJ.*>* <NN.*>+ <JJ.*>*)|(<JJ.*>))*}"
RULE_TINA   = "^((VBD,|VBG,|VBN,|CD.?,|JJ.?,|\?,){0,2}?(N.?.?,|\?,)+?(CD.,)??)\
               +?((PREP.?|DET.?,|IN.?,|CC.?,|\?,)((VBD,|VBG,|VBN,|CD.?,|JJ.?,|\?\
               ,){0,2}?(N.?.?,|\?,)+?)+?)*?$"


# ngram lists import/export parameters -----------------------------------------
DEFAULT_CSV_DELIM              = '\t'        # for import/export CSV defaults
DEFAULT_CSV_DELIM_GROUP        = '|&|'



# Files ----------------------------------------------------------------
import os
from .settings import BASE_DIR
# uploads/.gitignore prevents corpora indexing
# copora can be either a folder or symlink towards specific partition
UPLOAD_DIRECTORY   = os.path.join(BASE_DIR, 'uploads/corpora')
UPLOAD_LIMIT       = 1024 * 1024 * 1024
DOWNLOAD_DIRECTORY = UPLOAD_DIRECTORY

# Processing -----------------------------------------------------------
# about batch processing...
BATCH_PARSING_SIZE          = 256
BATCH_NGRAMSEXTRACTION_SIZE = 3000   # how many distinct ngrams before INTEGRATE


# Scrapers config
QUERY_SIZE_N_MAX     = 1000
QUERY_SIZE_N_DEFAULT = 1000


# Grammar rules for chunking
RULE_JJNN   = "{<JJ.*>*<NN.*|>+<JJ.*>*}"
RULE_NPN    = "{<JJ.*>*<NN.*>+((<P|IN> <DT>? <JJ.*>* <NN.*>+ <JJ.*>*)|(<JJ.*>))*}"
RULE_TINA   = "^((VBD,|VBG,|VBN,|CD.?,|JJ.?,|\?,){0,2}?(N.?.?,|\?,)+?(CD.,)??)\
               +?((PREP.?|DET.?,|IN.?,|CC.?,|\?,)((VBD,|VBG,|VBN,|CD.?,|JJ.?,|\?\
               ,){0,2}?(N.?.?,|\?,)+?)+?)*?$"


# ------------------------------------------------------------------------------
# Graph constraints to compute the graph:
# Modes: live graph generation, graph asynchronously computed or errors detected
# here are the maximum size of corpus and maplist required to compute the graph
graph_constraints = {'corpusMax' : 400
                    ,'corpusMin' : 10
                    ,'mapList'   : 50
                    }
