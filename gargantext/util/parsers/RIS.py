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
        "ER":  {"type": "delimiter"}, # the record delimiter
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
        hyperdata = {}
        last_key = None
        last_values = []

        for line in file:
            # bytes ~~> str
            line = line.decode("UTF-8").rstrip('\r\n')
            if len(line) >= 2 :
                # extract the parameter key...
                parameter_key = line[:2]

                # ...and keep the rest for when we know what to do with it
                current_value = line[self._begin:]

                # it's a new key => therefore the previous key is finished
                if parameter_key != last_key:

                    if last_key in self._parameters:
                        # translate key
                        parameter = self._parameters[last_key]
                        # 1 - we record the previous value array...
                        if parameter["type"] == "hyperdata":
                            separator = parameter["separator"] if "separator" in parameter else ""
                            hyperdata[parameter["key"]] = separator.join(last_values)

                        #... or even finish the record (rare here, most often after empty line)
                        elif parameter["type"] == "delimiter":
                            if 'language_fullname' not in hyperdata.keys():
                                if 'language_iso3' not in hyperdata.keys():
                                    if 'language_iso2' not in hyperdata.keys():
                                        hyperdata['language_iso2'] = 'en'
                            yield hyperdata
                            last_key = None
                            hyperdata = {}

                    # 2 - new key: also we start a new value array and move on to the next key
                    last_values = []
                    last_key = parameter_key

                # 3 - new key or old: in any case we feed the value array "buffer"
                try:
                    last_values.append(current_value)
                except Exception as error:
                    print(error)

            # empty line => we still need to check if PREVIOUS LINE was record delimiter
            else:
                # print("\n\n\nEMPTY LINE, with last_key", last_key)
                if last_key in self._parameters:
                    if parameter["type"] == "delimiter":
                        if 'language_fullname' not in hyperdata.keys():
                            if 'language_iso3' not in hyperdata.keys():
                                if 'language_iso2' not in hyperdata.keys():
                                    hyperdata['language_iso2'] = 'en'
                        yield hyperdata
                        last_key = None
                        hyperdata = {}

            # [end of loop per lines]

        # if a hyperdata object is left in memory, yield it as well
        if hyperdata:
            if 'language_fullname' not in hyperdata.keys():
                if 'language_iso3' not in hyperdata.keys():
                    if 'language_iso2' not in hyperdata.keys():
                        hyperdata['language_iso2'] = 'en'
            yield hyperdata
