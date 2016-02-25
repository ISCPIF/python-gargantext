# WARNING: to ensure consistency and retrocompatibility, lists should keep the
#   initial order (ie., new elements should be appended at the end of the lists)

from gargantext.util.lists import *

LISTTYPES = {
    'DOCUMENT': WeightedList,
    'SYNONYMS': Translations,
    'MIAMLIST': UnweightedList,
    'STOPLIST': UnweightedList,
    'COOCCURRENCES': WeightedMatrix,
}

NODETYPES = [
    None,
    # documents hierachy
    'USER',
    'PROJECT',
    'CORPUS',
    'DOCUMENT',
    # lists
    'SYNONYMS',
    'MIAMLIST',
    'STOPLIST',
    'COOCCURRENCES',
]


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
        # 'parser': RISParser,
        'default_language': 'en',
    },
    {   'name': 'Pubmed (XML format)',
        'parser': PubmedParser,
        'default_language': 'en',
    },
        {   'name': 'Scopus (RIS format)',
        # 'parser': RISParser,
        'default_language': 'en',
    },
    {   'name': 'Web of Science (ISI format)',
        # 'parser': ISIParser,
        'default_language': 'fr',
    },
    {   'name': 'Zotero (RIS format)',
        # 'parser': RISParser,
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
