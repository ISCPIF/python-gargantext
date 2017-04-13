"""
# WARNING: to ensure consistency and retrocompatibility, lists should keep the
#   initial order (ie., new elements should be appended at the end of the lists)

abstract:
---------
         something between global params, constants,
         configuration variables, ini file...

contents:
---------
      + database constants/ontology
         - nodetypes
            (db int <=> named types <=> python code)

      + low-level limits
         - query size
         - max upload size
         - doc parsing batch size
         - word extraction batch size

      + main process config
         - resourcetypes config (~ input ontology)
         - wordlist generation params
         - graph creation params
         - £TODO sequence of transformations "custom pipeline"

      + subprocess config
         - crawling, import
         - tagger services and functions
         - parser services
         - stemmer services

"""
import os
import re
import importlib
from gargantext.util.lists import *
from gargantext.util.tools import datetime, convert_to_date
from .settings import BASE_DIR

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


def get_nodetype_id_by_name(nodetype):
    '''resource :: name => resource dict'''
    for n in NODETYPES :
        if str(n["name"]) == str(sourcename):
            return n

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
# user parameters----------------------------------------
USER_LANG = ["fr", "en"]

# resources ---------------------------------------------
def get_resource(sourcetype):
    '''resource :: type => resource dict'''
    return RESOURCETYPES[sourcetype-1]

def get_resource_by_name(sourcename):
    '''resource :: name => resource dict'''
    for n in RESOURCETYPES:
        if str(n["name"]) == str(sourcename):
            return n
# taggers -----------------------------------------------
def get_tagger(lang):
    '''
    lang => observed language[0] => Tagger
    '''
    name = LANGUAGES[lang]["tagger"]
    module = "gargantext.util.taggers.%s" %(name)
    module = importlib.import_module(module, "")
    tagger = getattr(module, name)
    return tagger()




RESOURCETYPES = [
    {   "type": 1,
        'name': 'Europresse',
        'format': 'Europresse',
        'parser': "EuropresseParser",
        'file_formats':["zip", "txt"],
        'crawler': None,
    },
    {   'type': 2,
        'name': 'Jstor [RIS]',
        'format': 'RIS',
        'parser': "RISParser",
        'file_formats':["zip", "txt"],
        'crawler': None,
    },
    {   'type': 3,
        'name': 'Pubmed [CRAWLER/XML]',
        'format': 'Pubmed',
        'parser': "PubmedParser",
        'file_formats':["zip", "xml"],
        'crawler': "PubmedCrawler",
    },
    {   'type': 4,
        'name': 'Scopus [RIS]',
        'format': 'RIS',
        'parser': "RISParser",
        'file_formats':["zip", "txt"],
        'crawler': None,
    },
    {   'type': 5,
        'name': 'Web of Science [ISI]',
        'format': 'ISI',
        'parser': "ISIParser",
        'file_formats':["zip", "txt", "isi"],
        #'crawler': "ISICrawler",
        'crawler': None,
    },
    {   'type': 6,
        'name': 'Zotero [RIS]',
        'format': 'RIS',
        'parser': 'RISParser',
        'file_formats':["zip", "ris", "txt"],
        'crawler': None,
    },
    {   'type': 7,
        'name': 'CSV',
        'format': 'CSV',
        'parser': 'CSVParser',
        'file_formats':["zip", "csv"],
        'crawler': None,
    },
    {   'type': 8,
        'name': 'ISTex [CRAWLER]',
        'format': 'json',
        'parser': "ISTexParser",
        'file_formats':["zip", "txt"],
        'crawler': None,
    },
   {    "type": 9,
        "name": 'SCOAP [CRAWLER/XML]',
        "parser": "CernParser",
        "format": 'MARC21',
        'file_formats':["zip","xml"],
        "crawler": "CernCrawler",
   },
#   {    "type": 10,
#        "name": 'REPEC [RIS]',
#        "parser": "RISParser",
#        "format": 'RIS',
#        'file_formats':["zip","ris", "txt"],
#        "crawler": None,
#   },
#
   {    "type": 10,
        "name": 'REPEC [CRAWLER]',
        "parser": "MultivacParser",
        "format": 'JSON',
        'file_formats':["zip","json"],
        "crawler": "MultivacCrawler",
   },

]
#shortcut for resources declaration in template
PARSERS = [(n["type"],n["name"]) for n in RESOURCETYPES if n["parser"] is not None]
CRAWLERS = [(n["type"],n["name"]) for n in RESOURCETYPES if n["crawler"] is not None]

def load_parser(resource):
    '''given a resource load the corresponding Parser
    resource(dict) > Parser(object)
    exemple with resource ISTexParser
    PARSER filename: ISTEX
    PARSER object: ISTexParser
    '''
    filename = resource["parser"].replace("Parser", '').upper()
    module = 'gargantext.util.parsers.%s' %(filename)
    module = importlib.import_module(module)
    return getattr(module, resource["parser"])


def load_crawler(resource):
    '''given a resource load the corresponding Parser()
    resource(dict) > Parser(object)
    exemple with resource ISTexCrawler
    PARSER filename: ISTEX
    PARSER object: ISTexCrawler
    '''
    filename = resource["crawler"].replace("Crawler", "").upper()
    module = 'gargantext.util.crawlers.%s' %(filename)
    module = importlib.import_module(module)
    return getattr(module, resource["crawler"])



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
    return getattr(module, filename)()



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
# TAGGING options   -----------------------------------------
#activate lang detection?
DETECT_LANG = False
# Defaults INDEXED Fields for ngrams extraction
# put longest field first in order to make detection language more efficient
DEFAULT_INDEX_FIELDS            = ('abstract','title' )
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
# uploads/.gitignore prevents corpora indexing
# copora can be either a folder or symlink towards specific partition
UPLOAD_DIRECTORY   = os.path.join(BASE_DIR, 'uploads/corpora')
UPLOAD_LIMIT       = 1024 * 1024 * 1024
DOWNLOAD_DIRECTORY = UPLOAD_DIRECTORY

# Processing -----------------------------------------------------------
# about batch processing...
BATCH_PARSING_SIZE          = 256    # how many new docs before db write
BATCH_NGRAMSEXTRACTION_SIZE = 3000   # how many new node-ngram relations before INTEGRATE


# Scrapers config
QUERY_SIZE_N_MAX     = 1000
QUERY_SIZE_N_DEFAULT = 1000

# Refresh corpora workflow status for project view's progressbar
PROJECT_VIEW_REFRESH_INTERVAL  = 3000     # 1st refresh in ms (then increasing arithmetically)
PROJECT_VIEW_MAX_REFRESH_ATTEMPTS = 10    # how many times before we give up

# ------------------------------------------------------------------------------
# Graph <=> nodes API parameters
# number of relevant publications shown
DEFAULT_N_DOCS_HAVING_NGRAM = 5

# ------------------------------------------------------------------------------
# Graph constraints to compute the graph:
# Modes: live graph generation, graph asynchronously computed or errors detected
# here are the maximum size of corpus and maplist required to compute the graph
graph_constraints = {'corpusMax' : 0
                    ,'corpusMin' : 0
                    ,'mapList'   : 50
                    }
