import dateutil.parser
import zipfile
import re
import dateparser as date_parser
from gargantext.util.languages import languages
from gargantext.util import datetime, convert_to_datetime


class Parser:
    """Base class for performing files parsing depending on their type.
    """

    def __init__(self, file):
        self._file = self.open(file)

    def __del__(self):
        if hasattr(self, '_file'):
            self._file.close()

    def open(self, file):
        return open(file, 'rb') if isinstance(file, str) else file

    def detect_encoding(self, string):
        """Useful method to detect the encoding of a document.
        """
        import chardet
        encoding = chardet.detect(string)
        return encoding.get('encoding', 'UTF-8')

    def format_hyperdata_dates(self, hyperdata):
        """Format the dates found in the hyperdata.
        Examples:
            {"publication_date": "2014-10-23 09:57:42+00:00"}
            -> {"publication_date": "2014-10-23 09:57:42+00:00", "publication_year": "2014", ...}
            {"publication_year": "2014"}
            -> {"publication_date": "2014-01-01 00:00:00+00:00", "publication_year": "2014", ...}
        """

        # First, check the split dates...
        # This part mainly deal with Zotero data but can be usefull for others
        # parts
        date_string = hyperdata.get('publication_date_to_parse')
        if date_string is not None:
            date_string = re.sub(r'\/\/+(\w*|\d*)', '', date_string)
            try:
                hyperdata['publication_date'] = datetime.parse(date_string)
            except Exception as error:
                print(error, 'Date not parsed for:', date_string)
                hyperdata['publication_date'] = datetime.now()


        elif hyperdata.get('publication_year') is not None:

            prefixes = [key[:-5] for key in hyperdata.keys() if key[-5:] == "_year"]
            # eg prefixes : ['publication']

            for prefix in prefixes:
                date_string = hyperdata[prefix + "_year"]

                for part in ('month', 'day', 'hour', 'minute', 'second'):
                    key = prefix + '_' + part
                    if key not in hyperdata:
                        break

                    sep = ":" if key in ('minute', 'second') else " "
                    date_string += sep + hyperdata.get(key, '01')

                try:
                    hyperdata[prefix + "_date"] = dateutil.parser.parse(date_string)
                except Exception as error:
                    try:
                        print("_Parser: error in full date parse", error, date_string)
                        # Date format:  1994 NOV-DEC
                        hyperdata[prefix + "_date"] = date_parser.parse(str(date_string)[:8])

                    except Exception as error:
                        try:
                            print("_Parser: error in short date parse", error)
                            # FIXME Date format:  1994 SPR
                            # By default, we take the year only
                            hyperdata[prefix + "_date"] = date_parser.parse(str(date_string)[:4])

                        except Exception as error:
                            print("_Parser:", error)
        else:
            print("WARNING: Date unknown at _Parser level, using now()")
            hyperdata['publication_date'] = datetime.now()

        # ...then parse all the "date" fields, to parse it into separate elements
        prefixes = [key[:-5] for key in hyperdata.keys() if key[-5:] == "_date"]
        for prefix in prefixes:
            name = prefix + "_date"
            date = hyperdata[name]
            hyperdata[name] = str(convert_to_datetime(date))

            for part in ('year', 'month', 'day', 'hour', 'minute', 'second'):
                hyperdata[prefix + '_' + part] = getattr(date, part)

        # print("line 116", hyperdata['publication_date'])
        # finally, return the transformed result!
        return hyperdata


    def format_hyperdata_languages(self, hyperdata):
        """format the languages found in the hyperdata."""
        language = None
        language_keyerrors = {}
        for key in ('name', 'iso3', 'iso2', ):
            language_key = 'language_' + key
            if language_key in hyperdata:
                try:
                    language_symbol = hyperdata[language_key]
                    if language_symbol is not None:
                        language = languages[language_symbol]
                    if language:
                        break
                except KeyError:
                    language_keyerrors[key] = language_symbol

        # languages can find Language objects from any code iso2 or iso3
        # --------------------------------------------------------------
        # > languages['fr']
        # <Language iso3="fra" iso2="fr" implemented="True" name="French">
        # > languages['fra']
        # <Language iso3="fra" iso2="fr" implemented="True" name="French">
        if language is not None:
            hyperdata['language_name'] = language.name
            hyperdata['language_iso3'] = language.iso3
            if (language.iso2 is not None):
                # NB: language can be recognized through iso3 but have no iso2!!
                #     because there's *more* languages in iso3 codes (iso-639-3)
                # exemple:
                # > languages['dnj']
                # <Language iso3="dnj" iso2="None" implemented="False" name="Dan">
                #                            ----
                hyperdata['language_iso2'] = language.iso2
            else:
                # 'None' would become json 'null'  ==> "__unknown__" more stable
                hyperdata['language_iso2'] = "__unknown__"
        elif language_keyerrors:
            print('Unrecognized language: %s' % ', '.join(
                '%s="%s"' % (key, value) for key, value in language_keyerrors.items()
            ))
        return hyperdata

    def format_hyperdata(self, hyperdata):
        """Format the hyperdata."""
        hyperdata = self.format_hyperdata_dates(hyperdata)
        hyperdata = self.format_hyperdata_languages(hyperdata)
        return hyperdata

    def __iter__(self, file=None):
        """Parse the file, and its children files found in the file.
        C24B comment: le stokage/extraction du fichier devrait être faite en amont
        et cette methode est un peu obscure
        """
        if file is None:
            file = self._file
        # if the file is a ZIP archive, recurse on each of its files...
        if zipfile.is_zipfile(file):
            with zipfile.ZipFile(file) as zf:
                for filename in zf.namelist():
                    with zf.open(filename) as df, self.open(df) as f:
                        yield from self.__iter__(f)
        # ...otherwise, let's parse it directly!
        else:
            try:
                file.seek(0)
            except:pass
            # debug: print(self.parse)  # do we have correct parser ?
            for hyperdata in self.parse(file):
                yield self.format_hyperdata(hyperdata)
