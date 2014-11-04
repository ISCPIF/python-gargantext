from parsing.FileParsers.RisFileParser import RisFileParser


class IsiFileParser(RisFileParser):
    
    _parameters = {
        b"ER":  {"type": "delimiter"},
        b"TI":  {"type": "metadata", "key": "title", "separator": " "},
        b"AU":  {"type": "metadata", "key": "authors", "separator": ", "},
        b"DI":  {"type": "metadata", "key": "doi"},
        b"PY":  {"type": "metadata", "key": "publication_year"},
        b"PD":  {"type": "metadata", "key": "publication_month"},
        b"LA":  {"type": "metadata", "key": "language_fullname"},
        b"AB":  {"type": "metadata", "key": "abstract", "separator": " "},
        b"WC":  {"type": "metadata", "key": "fields"},
    }
