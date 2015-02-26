from django.db import transaction
from .FileParser import FileParser


class RisFileParser(FileParser):

    _parameters = {
        b"ER":  {"type": "delimiter"},
        b"TI":  {"type": "metadata", "key": "title", "separator": " "},
        b"AU":  {"type": "metadata", "key": "authors", "separator": ", "},
        b"UR":  {"type": "metadata", "key": "doi"},
        b"PY":  {"type": "metadata", "key": "publication_year"},
        b"PD":  {"type": "metadata", "key": "publication_month"},
        b"LA":  {"type": "metadata", "key": "language_iso2"},
        b"AB":  {"type": "metadata", "key": "abstract", "separator": " "},
        b"WC":  {"type": "metadata", "key": "fields"},
    }

    def _parse(self, file):
        metadata = {}
        last_key = None
        last_values = []
        # browse every line of the file
        for line in file:
            if len(line) > 2:
                # extract the parameter key
                parameter_key = line[:2]
                if parameter_key != b'  ' and parameter_key != last_key:
                    if last_key in self._parameters:
                        # translate the parameter key
                        parameter = self._parameters[last_key]
                        if parameter["type"] == "metadata":
                            separator = parameter["separator"] if "separator" in parameter else ""
                            metadata[parameter["key"]] = separator.join(last_values)
                        elif parameter["type"] == "delimiter":
                            if 'language_fullname' not in metadata.keys():
                                if 'language_iso3' not in metadata.keys():
                                    if 'language_iso2' not in metadata.keys():
                                        metadata['language_iso2'] = 'en'
                            yield metadata
                            metadata = {}
                    last_key = parameter_key
                    last_values = []
                try:
                    last_values.append(line[3:-1].decode())
                except Exception as error:
                    print(error)
        # if a metadata object is left in memory, yield it as well
        if metadata:
            yield metadata
