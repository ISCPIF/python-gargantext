NODETYPES = [
    None,
    'USER',
    'PROJECT',
    'CORPUS',
    'DOCUMENT',
]

LANGUAGES = {
    # 'fr': {
    #     'tagger': FrenchNgramsTagger
    # }
}


from gargantext.util.parsers import *

RESOURCETYPES = [
    # {   'name': 'CSV',
    #     # 'parser': CSVParser,
    #     'default_language': 'en',
    # },
    {   'name': 'Europress (English)',
        'parser': EuropressParser,
        'default_language': 'en',
    },
    {   'name': 'Europress (French)',
        # 'parser': EuropressParser,
        'default_language': 'fr',
    },
    # {   'name': 'ISTex',
    #     # 'parser': ISTexParser,
    #     'default_language': 'en',
    # },
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
]
