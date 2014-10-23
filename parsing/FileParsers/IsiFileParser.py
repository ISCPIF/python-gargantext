from django.db import transaction
from parsing.FileParsers.FileParser import FileParser


class IsiFileParser(FileParser):
    
    _parameters = {
        b"ER":  {"type": "delimiter"},
        b"TI":  {"type": "metadata", "key": "title", "concatenate": b" "},
        b"AU":  {"type": "metadata", "key": "authors", "concatenate": b", "},
        b"AB":  {"type": "metadata", "key": "abstract", "concatenate": b" "},
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
                            metadata[parameter["key"]] = parameter["concatenate"].join(last_values)
                        elif parameter["type"] == "delimiter":
                            print(metadata)
                            metadata = {}
                            break
                    last_key = parameter_key
                    last_values = []
                last_values.append(line[3:-1])
        self.file.close()