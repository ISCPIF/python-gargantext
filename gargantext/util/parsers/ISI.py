import re

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

        _year = re.compile(r'\b\d{4}\b')
        _season = re.compile(r'\b(SPR|SUM|FAL|WIN)\b', re.I)
        _month_interval = re.compile(r'\b([A-Z]{3})-([A-Z]{3})\b', re.I)
        _day_interval = re.compile(r'\b(\d{1,2})-(\d{1,2})\b')

        def _preprocess_PD(self, PD, PY):
            # Add a year to date if applicable
            if PY and self._year.search(PY) and not self._year.search(PD):
                PD = PY + " " + PD

            # Drop season if any
            PD = self._season.sub('', PD).strip()

            # If a month interval is present, keep only the first month
            PD = self._month_interval.sub(r'\1', PD)

            # If a day interval is present, keep only the first day
            PD = self._day_interval.sub(r'\1', PD)

            return PD

        def parse(self, file):
            PD = self._parameters["PD"]["key"]
            PY = self._parameters["PY"]["key"]

            for entry in super().parse(file):
                if PD in entry:
                    entry[PD] = self._preprocess_PD(entry[PD], entry[PY])

                yield entry
