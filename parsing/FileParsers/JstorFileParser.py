from .RisFileParser import RisFileParser


class JstorFileParser(RisFileParser):
 
    def __init__(self):
        super(RisFileParser, self).__init__()

        _parameters = {
            b"ER":  {"type": "delimiter"},
            b"TI":  {"type": "metadata", "key": "title", "separator": " "},
            b"AU":  {"type": "metadata", "key": "authors", "separator": ", "},
            b"UR":  {"type": "metadata", "key": "doi"},
            b"Y1":  {"type": "metadata", "key": "publication_year"},
            b"PD":  {"type": "metadata", "key": "publication_month"},
            b"LA":  {"type": "metadata", "key": "language_iso2"},
            b"AB":  {"type": "metadata", "key": "abstract", "separator": " "},
            b"WC":  {"type": "metadata", "key": "fields"},
        }

        begin = 3
