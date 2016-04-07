# WARNING: to ensure consistency and retrocompatibility, lists should keep the
#   initial order (ie., new elements should be appended at the end of the lists)

from gargantext.util.lists import *

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
]

# TODO find somewhere else than constants.py for function
import datetime
import dateutil
def convert_to_date(date):
    if isinstance(date, (int, float)):
        return datetime.datetime.timestamp(date)
    else:
        return dateutil.parser.parse(date)

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

    'text':
        { 'id'             : 7
        , 'type'           : str
        , 'convert_to_db'  : str
        , 'convert_from_db': str
        },

    'page':
        { 'id'             : 8
        , 'type'           : int
        , 'convert_to_db'  : int
        , 'convert_from_db': int
        },

}


from gargantext.util.taggers import *

LANGUAGES = {
    'en': {
        'tagger': EnglishMeltTagger,
        #'tagger': TurboTagger,
        #'tagger': NltkTagger,
    },
    'fr': {
        'tagger': FrenchMeltTagger,
        # 'tagger': TreeTagger,
    },
}


from gargantext.util.parsers import *

RESOURCETYPES = [
    {   'name': 'Europress (English)',
        'parser': EuropressParser,
        'default_language': 'en',
    },
    {   'name': 'Europress (French)',
        'parser': EuropressParser,
        'default_language': 'fr',
    },
    {   'name': 'Jstor (RIS format)',
        'parser': RISParser,
        'default_language': 'en',
    },
    {   'name': 'Pubmed (XML format)',
        'parser': PubmedParser,
        'default_language': 'en',
    },
    {   'name': 'Scopus (RIS format)',
        'parser': RISParser,
        'default_language': 'en',
    },
    {   'name': 'Web of Science (ISI format)',
        'parser': ISIParser,
        'default_language': 'fr',
    },
    {   'name': 'Zotero (RIS format)',
        'parser': RISParser,
        'default_language': 'en',
    },
    {   'name': 'CSV',
        'parser': CSVParser,
        'default_language': 'en',
    },
    {   'name': 'ISTex',
        'parser': ISTexParser,
        'default_language': 'en',
    },
]

# linguistic extraction parameters ---------------------------------------------
DEFAULT_TFIDF_CUTOFF_RATIO      = .45        # MAINLIST maximum terms in %

DEFAULT_TFIDF_HARD_LIMIT        = 750        # MAINLIST maximum terms abs
                                             # (makes COOCS larger ~ O(N²) /!\)

DEFAULT_COOC_THRESHOLD          = 3          # inclusive minimum for COOCS coefs
                                             # (makes COOCS more sparse)

DEFAULT_MAPLIST_MAX             = 300        # MAPLIST maximum terms

DEFAULT_MAPLIST_MONOGRAMS_RATIO = .5         # part of monograms in MAPLIST

DEFAULT_MAX_NGRAM_LEN = 7                    # limit used after POStagging rule
                                             # (initial ngrams number is a power law of this /!\)
                                             # (and most longer ngrams have tiny freq anyway)

DEFAULT_ALL_LOWERCASE_FLAG = True            # lowercase ngrams before recording
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
UPLOAD_DIRECTORY   = os.path.join(BASE_DIR, 'uploads')
UPLOAD_LIMIT       = 1024 * 1024 * 1024
DOWNLOAD_DIRECTORY = UPLOAD_DIRECTORY


# about batch processing...
BATCH_PARSING_SIZE          = 256
BATCH_NGRAMSEXTRACTION_SIZE = 1024
