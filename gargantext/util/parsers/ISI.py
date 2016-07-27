from .RIS import RISParser


class ISIParser(RISParser):

        _begin = 3

        _parameters = {
            b"ER":  {"type": "delimiter"},
            b"TI":  {"type": "hyperdata", "key": "title", "separator": " "},
            b"AU":  {"type": "hyperdata", "key": "authors", "separator": ", "},
            b"DI":  {"type": "hyperdata", "key": "doi"},
            b"SO":  {"type": "hyperdata", "key": "journal"},
            b"PY":  {"type": "hyperdata", "key": "publication_year"},
            b"PD":  {"type": "hyperdata", "key": "publication_month"},
            b"LA":  {"type": "hyperdata", "key": "language_fullname"},
            b"AB":  {"type": "hyperdata", "key": "abstract", "separator": " "},
            b"WC":  {"type": "hyperdata", "key": "fields"},
        }
