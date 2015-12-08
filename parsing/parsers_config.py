# import * via __init__.py
from .FileParsers import *

parsers = {
        'Pubmed (xml format)'               : PubmedFileParser,
        'Web of Science (ISI format)'       : IsiFileParser,
        'Scopus (RIS format)'               : RisFileParser,
        'Zotero (RIS format)'               : ZoteroFileParser,
        'Jstor (RIS format)'                : JstorFileParser,
        
        'Europress (French)'                : EuropressFileParser,
        'Europress (English)'               : EuropressFileParser,
        
        # Une seule entrée pourra remplacer les variantes French/English
        # mais (TODO) il faudra juste vérifier cohérence:
        #   - avec DB: node_resourcetype
        #   - avec admin/update_corpus.py
        #'Europress'                        : EuropressFileParser,

        'CSVParser'                         : CSVParser,
        'ISTex'                             : ISTex,
    }

