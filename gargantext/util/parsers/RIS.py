from ._Parser import Parser
from gargantext.util.languages import languages
from re import match

class RISParser(Parser):

    _begin = 6
    _parameters = {
        "ER":  {"type": "delimiter"}, # the record delimiter

        "TI":  {"type": "hyperdata", "key": "title", "separator": " "},
        "T1":  {"type": "hyperdata", "key": "title", "separator": " "},
        # "T1": variant of TI (if together only last will be kept)

        "ST":  {"type": "hyperdata", "key": "subtitle", "separator": " "},
        "AU":  {"type": "hyperdata", "key": "authors", "separator": "\n"},

        "JO":  {"type": "hyperdata", "key": "journal"},
        "T2":  {"type": "hyperdata", "key": "journal"},
        # "T2": variant of JO (if together only last will be kept)

        "UR":  {"type": "hyperdata", "key": "doi"},

        # RIS format specifications: PY is not only year but YYYY/MM/DD with MM and DD optional
        #                            cf. https://en.wikipedia.org/wiki/RIS_(file_format)
        "PY":  {"type": "hyperdata", "key": "publication_year"},

        "N1":  {"type": "hyperdata", "key": "references", "separator": ", "}, # more like notes in reality
        "LA":  {"type": "hyperdata", "key": "language_iso2"},
        "AB":  {"type": "hyperdata", "key": "abstract", "separator": " "},

        # TODO other interesting fields
        # "KW"            (keywords)
        # "A1", "A2"...   (variants of AU)
        # "N2"            (variant of AB)

        # previously mentioned here but in fact not in RIS specifications
        # "PD":  {"type": "hyperdata", "key": "publication_month"},
        # "WC":  {"type": "hyperdata", "key": "fields"},
    }

    def parse(self, file):
        hyperdata = {}
        last_key = None
        last_values = []
        current_value = None

        for line in file:
            # bytes ~~> str
            line = line.decode("UTF-8").rstrip('\r\n')

            # print("RIS line:", line)

            if len(line) >= 2 :
                # print("(nonemptyline)")

                # test if key line (otherwise: continuation line)
                if match(r'[A-Z][A-Z0-9]', line):
                    parameter_key = line[:2]
                    # print("(matchparamline:"+parameter_key+")")

                    # we can now be sure that the value is rest of the line
                    # (keep it for when we know what to do with it)
                    current_value = line[self._begin:]

                    # it's a new key => therefore the previous key is finished
                    if parameter_key != last_key:

                        if last_key in self._parameters:
                            # translate key
                            parameter = self._parameters[last_key]
                            # 1 - we record the previous value array...
                            if parameter["type"] == "hyperdata":
                                separator = parameter["separator"] if "separator" in parameter else ""
                                final_value = separator.join(last_values)
                                if last_key != 'PY':
                                    hyperdata[parameter["key"]] = final_value
                                else:
                                    hyperdata = PY_values_decompose_and_save(final_value, hyperdata)
                                # print("{saved previous"+last_key+"}")

                            #... or even finish the record (rare here, most often after empty line)
                            elif parameter["type"] == "delimiter":
                                if 'language_fullname' not in hyperdata.keys():
                                    if 'language_iso3' not in hyperdata.keys():
                                        if 'language_iso2' not in hyperdata.keys():
                                            hyperdata['language_iso2'] = 'en'
                                yield hyperdata
                                # print("{saved previous record}")
                                last_key = None
                                hyperdata = {}

                        # 2 - new key: also we start a new value array and move on to the next key
                        last_values = []
                        last_key = parameter_key

                # continuation line: values start from position 0
                else:
                    current_value = line
                    # print("(continuationline)")


                # 3 - new key or old or no key: in any case we pass contents to
                #     the value array buffer (=> for the next loop only)
                last_values.append(current_value)
                current_value = None

            # empty line => we need to check if PREVIOUS LINE was record delimiter
            else:
                # print("(emptyline)")
                if last_key in self._parameters:
                    if parameter["type"] == "delimiter":
                        if 'language_fullname' not in hyperdata.keys():
                            if 'language_iso3' not in hyperdata.keys():
                                if 'language_iso2' not in hyperdata.keys():
                                    hyperdata['language_iso2'] = 'en'
                        yield hyperdata
                        # print("{saved previous record}")
                        last_key = None
                        hyperdata = {}
            # [end of loop per lines]

        # if we have any values left on previous line => put them in hd
        if last_key in self._parameters:
            parameter = self._parameters[last_key]
            if parameter["type"] == "hyperdata":
                separator = parameter["separator"] if "separator" in parameter else ""
                final_value = separator.join(last_values)
                if last_key != 'PY':
                    hyperdata[parameter["key"]] = final_value
                else:
                    hyperdata = PY_values_decompose_and_save(final_value, hyperdata)
                # print("{saved previous"+last_key+"}")

        # if a hyperdata object is left in memory, yield it as well
        if hyperdata:
            if 'language_fullname' not in hyperdata.keys():
                if 'language_iso3' not in hyperdata.keys():
                    if 'language_iso2' not in hyperdata.keys():
                        hyperdata['language_iso2'] = 'en'
            yield hyperdata
            # print("{saved previous record}")



# helper function for PY dates
def PY_values_decompose_and_save(ris_date_str, hyperdata):
    """
    PY is associated to our publication_year, but the exact format is:
              "YYYY/MM/DD/"         (with MM and DD optional)

    exemple contents:
        1948/07/01
        1948/07/01/
        1948/07//
        1948//
        1948

    => This function does the necessary additional date subparsing
       and saves the results in the 3 hyperdata slots: year, month, day
    """
    possible_fields = ['publication_year',
                       'publication_month',
                       'publication_day',
                       None]
    current_field_i = 0
    buffr = ""

    for char in ris_date_str:
        if char != '/':
            # continue reading
            buffr += char
        else:
            # on '/' => we save and shift to next field
            current_field = possible_fields[current_field_i]
            if len(buffr):
                hyperdata[current_field] = buffr
            # prepare for next time
            current_field_i += 1
            buffr = ""

    # save at the end too
    current_field = possible_fields[current_field_i]
    if len(buffr):
        hyperdata[current_field] = buffr

    # return updated meta
    return hyperdata
