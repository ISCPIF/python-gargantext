from .RisFileParser import RisFileParser

from ..Caches import LanguagesCache

class ZoteroFileParser(RisFileParser):
    def __init__(self):
        super(RisFileParser, self).__init__()

        self._begin = 6

        self._parameters = {
            b"ER":  {"type": "delimiter"},
            b"TI":  {"type": "hyperdata", "key": "title", "separator": " "},
            b"AU":  {"type": "hyperdata", "key": "authors", "separator": ", "},
            b"T2":  {"type": "hyperdata", "key": "journal"},
            b"UR":  {"type": "hyperdata", "key": "doi"},
            b"DA":  {"type": "hyperdata", "key": "publication_date_to_parse"},
            b"PY":  {"type": "hyperdata", "key": "publication_year"},
            b"PD":  {"type": "hyperdata", "key": "publication_month"},
            b"LA":  {"type": "hyperdata", "key": "language_iso2"},
            b"AB":  {"type": "hyperdata", "key": "abstract", "separator": " "},
            b"WC":  {"type": "hyperdata", "key": "fields"},
        }

