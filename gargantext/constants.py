# WARNING: to ensure consistency and retrocompatibility, lists should keep the
#   initial order (ie., new elements should be appended at the end of the lists)

from gargantext.util.lists import *

LISTTYPES = {
    'DOCUMENT'     : WeightedList,
    'GROUPLIST'    : Translations,
    'STOPLIST'     : UnweightedList,
    'MAINLIST'     : UnweightedList,
    'MAPLIST'      : UnweightedList,
    'OCCURRENCES'  : WeightedList,
    'COOCCURRENCES': WeightedMatrix,
}

NODETYPES = [
    None,
    # documents hierarchy
    'USER',
    'PROJECT',
    'CORPUS',
    'DOCUMENT',
    # lists
    'STOPLIST',
    'GROUPLIST',
    'MAINLIST',
    'MAPLIST',
    'COOCCURRENCES',
    # scores
    'OCCURRENCES',
    'SPECIFICITY',
    'CVALUE',
    'TFIDF-CORPUS',
    'TFIDF-GLOBAL',
]

import datetime
import dateutil
def convert_to_date(date):
    if isinstance(date, (int, float)):
        return datetime.datetime.timestamp(date)
    else:
        return dateutil.parser.parse(date)

INDEXED_HYPERDATA = {
    'publication_date':
        {'id': 1, 'type': datetime.datetime, 'convert_to_db': convert_to_date, 'convert_from_db': datetime.datetime.fromtimestamp},
    'title':
        {'id': 2, 'type': str, 'convert_to_db': str, 'convert_from_db': str},
    'count':
        {'id': 3, 'type': int, 'convert_to_db': float, 'convert_from_db': int},
}


from gargantext.util.taggers import *

LANGUAGES = {
    'en': {
        'tagger': TurboTagger,
        # 'tagger': EnglishMeltTagger,
        # 'tagger': NltkTagger,
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
    # {   'name': 'CSV',
    #     # 'parser': CSVParser,
    #     'default_language': 'en',
    # },
    # {   'name': 'ISTex',
    #     # 'parser': ISTexParser,
    #     'default_language': 'en',
    # },
]


# other parameters
# default number of docs POSTed to scrappers.views.py
#  (at page  project > add a corpus > scan/process sample)
QUERY_SIZE_N_DEFAULT = 1000

import os
from .settings import BASE_DIR
UPLOAD_DIRECTORY = os.path.join(BASE_DIR, 'uploads')
UPLOAD_LIMIT = 1024 * 1024 * 1024
DOWNLOAD_DIRECTORY = UPLOAD_DIRECTORY


# about batch processing...
BATCH_PARSING_SIZE = 256
BATCH_NGRAMSEXTRACTION_SIZE = 1024
