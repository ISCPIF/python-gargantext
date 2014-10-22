from django.db import transaction
from parsing.FileParsers.FileParser import FileParser


class IsiFileParser(FileParser):
    
    _parameters = {
        "ER":   {"type": "delimiter"},
        "AU":   {"type": "metadata", "key": "authors", "concatenate": False},
        "AB":   {"type": "metadata", "key": "abstract", "concatenate": True},
    }
    
    def parse(self, parentNode=None, tag=True):
        metadata = {}
        last_key = None
        last_values = []
        for line in self.file:
            if len(line) > 2:
                parameter_key = line[:2]
                if parameter_key != last_key:
                    if last_key is not None:
                        parameter = self._parameters[last_key]
                        if parameter["type"] == "metadata":
                            metadata[parameter["key"]] = ' '.join(last_values) if parameter["concatenate"] else last_values
                        elif parameter["type"] == "metadata":
                            print(metadata)
                            metadata = {}
                            break
                    parameter = self._parameters[last_key]
                    last_key = parameter_key
                    last_values = []
                last_values.append(line[3:-1])