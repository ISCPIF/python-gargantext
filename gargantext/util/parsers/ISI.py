from .RIS import RISParser


class ISIParser(RISParser):

        _begin = 3

        _parameters = {
            "ER":  {"type": "delimiter"},
            "TI":  {"type": "hyperdata", "key": "title", "separator": " "},
            "AU":  {"type": "hyperdata", "key": "authors", "separator": ", "},
            "DI":  {"type": "hyperdata", "key": "doi"},
            "SO":  {"type": "hyperdata", "key": "journal"},
            "PY":  {"type": "hyperdata", "key": "publication_year"},
            "PD":  {"type": "hyperdata", "key": "publication_month"},
            "LA":  {"type": "hyperdata", "key": "language_fullname"},
            "AB":  {"type": "hyperdata", "key": "abstract", "separator": " "},
            "WC":  {"type": "hyperdata", "key": "fields"},
        }
