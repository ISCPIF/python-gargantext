from ._Parser import Parser

from gargantext.util.languages import languages

#from admin.utils import PrintException

class RISParser(Parser):

#    def __init__(self, language_cache=None):
#
#        #super(Parser, self).__init__()
#        #super(Parser, self).__init__()
#        self._languages_cache = LanguagesCache() if language_cache is None else language_cache


    _begin = 6
    _parameters = {
        "ER":  {"type": "delimiter"},
        "TI":  {"type": "hyperdata", "key": "title", "separator": " "},
        "ST":  {"type": "hyperdata", "key": "subtitle", "separator": " "},
        "AU":  {"type": "hyperdata", "key": "authors", "separator": "\n"},
        "T2":  {"type": "hyperdata", "key": "journal"},
        "UR":  {"type": "hyperdata", "key": "doi"},
        "PY":  {"type": "hyperdata", "key": "publication_year"},
        "PD":  {"type": "hyperdata", "key": "publication_month"},
        "N1":  {"type": "hyperdata", "key": "references", "separator": ", "},
        "LA":  {"type": "hyperdata", "key": "language_iso2"},
        "A":  {"type": "hyperdata", "key": "abstract", "separator": " "},
        "WC":  {"type": "hyperdata", "key": "fields"},
    }

    def parse(self, file):
        print("=====> PARSING RIS", file)
        hyperdata = {}
        last_key = None
        last_values = []
        for line in file:
            # bytes ~~> str
            line = line.decode("UTF-8").rstrip('\r\n')
            if len(line) > 2 :
                # extract the parameter key
                parameter_key = line[:2]
                if parameter_key != '  ' and parameter_key != last_key:
                    if last_key in self._parameters:
                        # translate the parameter key
                        parameter = self._parameters[last_key]
                        if parameter["type"] == "hyperdata":
                            separator = parameter["separator"] if "separator" in parameter else ""
                            hyperdata[parameter["key"]] = separator.join(last_values)
                        elif parameter["type"] == "delimiter":
                            if 'language_fullname' not in hyperdata.keys():
                                if 'language_iso3' not in hyperdata.keys():
                                    if 'language_iso2' not in hyperdata.keys():
                                        hyperdata['language_iso2'] = 'en'
                            yield hyperdata
                            hyperdata = {}
                    last_key = parameter_key
                    last_values = []
                try:
                    last_values.append(line[self._begin:])
                except Exception as error:
                    print(error)
        # if a hyperdata object is left in memory, yield it as well
        if hyperdata:
            yield hyperdata
