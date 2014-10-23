from django.db import transaction
from parsing.FileParsers.FileParser import FileParser


class IsiFileParser(FileParser):
    
    _parameters = {
        b"ER":  {"type": "delimiter"},
        b"TI":  {"type": "metadata", "key": "title", "separator": b" "},
        b"AU":  {"type": "metadata", "key": "authors", "separator": b", "},
        b"DI":  {"type": "metadata", "key": "doi"},
        b"LA":  {"type": "metadata", "key": "language"},
        b"AB":  {"type": "metadata", "key": "abstract", "separator": b" "},
    }
    
    def parse(self, parentNode=None, tag=True):
        metadata = {}
        last_key = None
        last_values = []
        for line in self._file:
            if len(line) > 2:
                parameter_key = line[:2]
                if parameter_key != b'  ' and parameter_key != last_key:
                    if last_key in self._parameters:
                        parameter = self._parameters[last_key]
                        if parameter["type"] == "metadata":
                            separator = parameter["separator"] if "separator" in parameter else b""
                            metadata[parameter["key"]] = separator.join(last_values)
                        elif parameter["type"] == "delimiter":
                            language = self._languages_fullname[metadata["language"].lower().decode()]
                            # self.create_document(
                                # parentNode  = parentNode,
                                # title       = metadata["title"],
                                # contents    = metadata["abstract"],
                                # language    = language,
                                # metadata    = metadata,
                                # guid        = metadata["guid"]
                            # )
                            print(metadata)
                            print()
                            metadata = {}
                    last_key = parameter_key
                    last_values = []
                last_values.append(line[3:-1])
        self._file.close()

