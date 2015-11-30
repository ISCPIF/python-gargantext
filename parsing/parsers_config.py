from .FileParsers import *

parsers = {
        'Pubmed (xml format)'               : PubmedFileParser,
        'Web of Science (ISI format)'       : IsiFileParser,
        'Scopus (RIS format)'               : RisFileParser,
        'Zotero (RIS format)'               : ZoteroFileParser,
        'Jstor (RIS format)'                : JstorFileParser,
        'Europress (old corpora)'           : EuropressFileParser,
        'Europress (French)'                : EuropressFileParser_fr,
        'Europress (English)'               : EuropressFileParser_en,
        'CSVParser'                         : CSVParser,
        'ISTex'                             : ISTex,
    }

