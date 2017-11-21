from .RIS import RISParser


class ISIParser(RISParser):

        _begin = 3

        _parameters = {
            "ER":  {"type": "delimiter"},
            "TI":  {"type": "hyperdata", "key": "title", "separator": " "},
            "AU":  {"type": "hyperdata", "key": "authors", "separator": ", "},
            "DI":  {"type": "hyperdata", "key": "doi"},
            "SO":  {"type": "hyperdata", "key": "source"},
            "PY":  {"type": "hyperdata", "key": "publication_year"},
            "PD":  {"type": "hyperdata", "key": "publication_date_to_parse"},
            "LA":  {"type": "hyperdata", "key": "language_fullname"},
            "AB":  {"type": "hyperdata", "key": "abstract", "separator": " "},
            "WC":  {"type": "hyperdata", "key": "fields"},
        }
