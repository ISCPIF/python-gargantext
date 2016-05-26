# WARNING: to ensure consistency and retrocompatibility, lists should keep the
#   initial order (ie., new elements should be appended at the end of the lists)

from gargantext.util.lists import *
from gargantext.util.tools import datetime, convert_to_date

import re

LISTTYPES = {
    'DOCUMENT'     : WeightedList,
    'GROUPLIST'    : Translations,
    'STOPLIST'     : UnweightedList,
    'MAINLIST'     : UnweightedList,
    'MAPLIST'      : UnweightedList,
    'SPECIFICITY'  : WeightedList,
    'OCCURRENCES'  : WeightedContextIndex,
    'COOCCURRENCES': WeightedMatrix,
    'TFIDF-CORPUS' : WeightedContextIndex,
    'TFIDF-GLOBAL' : WeightedContextIndex,
}

NODETYPES = [
    None,
    # documents hierarchy
    'USER',                  # 1
    'PROJECT',               # 2
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
    'SPECIFICITY',           # 11
    'CVALUE',                # 12
    'TFIDF-CORPUS',          # 13
    'TFIDF-GLOBAL',          # 14
    # docs subset
    'FAVORITES'              # 15
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


#from gargantext.util.taggers import FrenchMeltTagger, TurboTagger
from gargantext.util.taggers import NltkTagger
LANGUAGES = {
    'en': {
        #'tagger': EnglishMeltTagger,
        #'tagger': TurboTagger,
        'tagger': NltkTagger,
    },
    'fr': {
        #'tagger': FrenchMeltTagger,
        # 'tagger': TreeTagger,
        'tagger': NltkTagger,
    },
}


from gargantext.util.parsers import \
    EuropressParser, RISParser, PubmedParser, ISIParser, CSVParser, ISTexParser, CernParser

from gargantext.util.scrappers import \
    CernScraper


def get_resource(corpus_type):
    '''get ressources values for a given ressource_type id'''
    return [n for n in RESOURCES_TYPE if n["type"] == corpus_type][0]

RESOURCETYPES = [
    # type 0
    {   'type':0,
        'name': 'Select database below',
        'parser': None,
        'default_language': None,
    },
    # type 1
    {   'type':1,
        'name': 'Europress (English)',
        'parser': EuropressParser,
        'default_language': 'en',
        'accepted_formats':["zip",],
    },
    # type 2
    {   'type':2,
        'name': 'Europress (French)',
        'parser': EuropressParser,
        'default_language': 'fr',
        'accepted_formats':["zip",],
    },
    # type 3
    {   'type':3,
        'name': 'Jstor (RIS format)',
        'parser': RISParser,
        'default_language': 'en',
        'accepted_formats':["zip",],
    },
    # type 4
    {   'type':4,
        'name': 'Pubmed (XML format)',
        'parser': PubmedParser,
        'default_language': 'en',
        'accepted_formats':["zip",],
    },
    # type 5
    {   'type':5,
        'name': 'Scopus (RIS format)',
        'parser': RISParser,
        'default_language': 'en',
        'accepted_formats':["zip",],
    },
    # type 6
    {   'type': 6,
        'name': 'Web of Science (ISI format)',
        'parser': ISIParser,
        'default_language': 'en',
        'accepted_formats':["zip",],
    },
    # type 7
    {   'type':7,
        'name': 'Zotero (RIS format)',
        'parser': RISParser,
        'default_language': 'en',
        'accepted_formats':["zip",],
    },
    # type 8
    {   'type':8,
        'name': 'CSV',
        'parser': CSVParser,
        'default_language': 'en',
        'accepted_formats':["csv"],
    },
    # type 9
    {   "type":9,
        'name': 'ISTex',
        'parser': ISTexParser,
        'default_language': 'en',
        'accepted_formats':["zip",],
    },
    # type 10
   {    "type":10,
        "name": 'SCOAP (XML MARC21 Format)',
        "parser": CernParser,
        "default_language": "en",
        'accepted_formats':["zip","xml"],
        "scrapper": CernScrapper,
        "base_url": "http://api.scoap3.org/search?",
   },
]


# linguistic extraction parameters ---------------------------------------------
DEFAULT_TFIDF_CUTOFF_RATIO      = .75        # MAINLIST maximum terms in %

DEFAULT_TFIDF_HARD_LIMIT        = 5000       # MAINLIST maximum terms abs
                                             # (makes COOCS larger ~ O(N²) /!\)

DEFAULT_COOC_THRESHOLD          = 2          # inclusive minimum for COOCS coefs
                                             # (makes COOCS more sparse)

DEFAULT_MAPLIST_MAX             = 350        # MAPLIST maximum terms

DEFAULT_MAPLIST_MONOGRAMS_RATIO = .15         # part of monograms in MAPLIST

DEFAULT_MAX_NGRAM_LEN           = 7          # limit used after POStagging rule
                                             # (initial ngrams number is a power law of this /!\)
                                             # (and most longer ngrams have tiny freq anyway)

DEFAULT_ALL_LOWERCASE_FLAG      = True       # lowercase ngrams before recording
                                             # them to their DB table
                                             # (potentially bad for acronyms but
                                             #  good for variants like same term
                                             #  occurring at sentence beginning)

# ------------------------------------------------------------------------------
# other parameters

# default number of docs POSTed to scrappers.views.py
#  (at page  project > add a corpus > scan/process sample)
QUERY_SIZE_N_DEFAULT = 1000

import os
from .settings import BASE_DIR
# uploads/.gitignore prevents corpora indexing
# copora can be either a folder or symlink towards specific partition
UPLOAD_DIRECTORY   = os.path.join(BASE_DIR, 'uploads/corpora')
UPLOAD_LIMIT       = 1024* 1024 * 1024
DOWNLOAD_DIRECTORY = UPLOAD_DIRECTORY


# about batch processing...
BATCH_PARSING_SIZE          = 256
BATCH_NGRAMSEXTRACTION_SIZE = 1024


# Scrapers config
QUERY_SIZE_N_MAX     = 1000
QUERY_SIZE_N_DEFAULT = 1000


# Grammar rules for chunking
RULE_JJNN   = "{<JJ.*>*<NN.*|>+<JJ.*>*}"
RULE_JJDTNN = "{<JJ.*>*<NN.*>+((<P|IN> <DT>? <JJ.*>* <NN.*>+ <JJ.*>*)|(<JJ.*>))*}"
RULE_TINA   = "^((VBD,|VBG,|VBN,|CD.?,|JJ.?,|\?,){0,2}?(N.?.?,|\?,)+?(CD.,)??)\
               +?((PREP.?|DET.?,|IN.?,|CC.?,|\?,)((VBD,|VBG,|VBN,|CD.?,|JJ.?,|\?\
               ,){0,2}?(N.?.?,|\?,)+?)+?)*?$"
