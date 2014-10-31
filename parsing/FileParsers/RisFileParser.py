from django.db import transaction
from parsing.FileParsers.FileParser import FileParser


class RisFileParser(FileParser):

    _parameters = {
        b"TY":  {"type": "delimiter"},
        b"TI":  {"type": "metadata", "key": "title", "separator": " "},
        b"AU":  {"type": "metadata", "key": "authors", "separator": ", "},
        b"DI":  {"type": "metadata", "key": "doi"},
        b"PY":  {"type": "metadata", "key": "publication_year"},
        b"PD":  {"type": "metadata", "key": "publication_month"},
        b"LA":  {"type": "metadata", "key": "language"},
        b"AB":  {"type": "metadata", "key": "abstract", "separator": " "},
        b"WC":  {"type": "metadata", "key": "fields"},
    }

    def _parse(self, file):
        metadata_list = []
        metadata = {}
        last_key = None
        last_values = []
        for line in file:
            if len(line) > 2:
                parameter_key = line[:2]
                if parameter_key != b'  ' and parameter_key != last_key:
                    if last_key in self._parameters:
                        parameter = self._parameters[last_key]
                        if parameter["type"] == "metadata":
                            separator = parameter["separator"] if "separator" in parameter else ""
                            metadata[parameter["key"]] = separator.join(last_values)
                        elif parameter["type"] == "delimiter":
                            #language = self._languages_fullname[metadata["language"].lower()]
                            metadata_list.append(metadata)
                    last_key = parameter_key
                    last_values = []
                last_values.append(line[3:-1].decode())
        return metadata_list
