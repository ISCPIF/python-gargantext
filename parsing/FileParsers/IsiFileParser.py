from .RisFileParser import RisFileParser



class IsiFileParser(RisFileParser):
    
    def __init__(self):
        
        super(RisFileParser, self).__init__()
        
        self._begin = 3
        
        self._parameters = {
            b"ER":  {"type": "delimiter"},
            b"TI":  {"type": "hyperdata", "key": "title", "separator": " "},
            b"AU":  {"type": "hyperdata", "key": "authors", "separator": ", "},
            b"DI":  {"type": "hyperdata", "key": "doi"},
            b"PY":  {"type": "hyperdata", "key": "publication_year"},
            b"PD":  {"type": "hyperdata", "key": "publication_month"},
            b"LA":  {"type": "hyperdata", "key": "language_fullname"},
            b"AB":  {"type": "hyperdata", "key": "abstract", "separator": " "},
            b"WC":  {"type": "hyperdata", "key": "fields"},
        }

