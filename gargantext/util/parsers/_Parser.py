import datetime
import dateutil.parser
import zipfile
import re

import dateparser as date_parser
from gargantext.util.languages import languages


DEFAULT_DATE = datetime.datetime(datetime.MINYEAR, 1, 1)


class Parser:
    """Base class for performing files parsing depending on their type.
    """

    def __init__(self, file):
        if isinstance(file, str):
            self._file = open(file, 'rb')
        else:
            self._file = file

    def __del__(self):
        self._file.close()

    def detect_encoding(self, string):
        """Useful method to detect the encoding of a document.
        """
        import chardet
        encoding = chardet.detect(string)
        return encoding.get('encoding', 'UTF-8')

    def format_hyperdata_dates(self, hyperdata):
        """Format the dates found in the hyperdata.
        Examples:
            {"publication_date": "2014-10-23 09:57:42"}
            -> {"publication_date": "2014-10-23 09:57:42", "publication_year": "2014", ...}
            {"publication_year": "2014"}
            -> {"publication_date": "2014-01-01 00:00:00", "publication_year": "2014", ...}
        """

        # First, check the split dates...
        # This part mainly deal with Zotero data but can be usefull for others
        # parts
        date_string = hyperdata.get('publication_date_to_parse', None)
        if date_string is not None:
            date_string = re.sub(r'\/\/+(\w*|\d*)', '', date_string)
            try:
                hyperdata['publication' + "_date"] = dateutil.parser.parse(
                    date_string,
                    default=DEFAULT_DATE
                ).strftime("%Y-%m-%d %H:%M:%S")
            except Exception as error:
                print(error, 'Date not parsed for:', date_string)
                hyperdata['publication_date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


        elif hyperdata.get('publication_year', None) is not None:
            prefixes = [key[:-5] for key in hyperdata.keys() if key[-5:] == "_year"]
            for prefix in prefixes:
                date_string = hyperdata[prefix + "_year"]
                key = prefix + "_month"
                if key in hyperdata:
                    date_string += " " + hyperdata[key]
                    key = prefix + "_day"
                    if key in hyperdata:
                        date_string += " " + hyperdata[key]
                        key = prefix + "_hour"
                        if key in hyperdata:
                            date_string += " " + hyperdata[key]
                            key = prefix + "_minute"
                            if key in hyperdata:
                                date_string += ":" + hyperdata[key]
                                key = prefix + "_second"
                                if key in hyperdata:
                                    date_string += ":" + hyperdata[key]
                try:
                    hyperdata[prefix + "_date"] = dateutil.parser.parse(date_string).strftime("%Y-%m-%d %H:%M:%S")
                except Exception as error:
                    try:
                        print(error, date_string)
                        # Date format:  1994 NOV-DEC
                        hyperdata[prefix + "_date"] = date_parser.parse(str(date_string)[:8]).strftime("%Y-%m-%d %H:%M:%S")

                    except Exception as error:
                        try:
                            print(error)
                            # FIXME Date format:  1994 SPR
                            # By default, we take the year only
                            hyperdata[prefix + "_date"] = date_parser.parse(str(date_string)[:4]).strftime("%Y-%m-%d %H:%M:%S")

                        except Exception as error:
                            print(error)
        else:
            print("WARNING: Date unknown at _Parser level, using now()")
            hyperdata['publication_date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ...then parse all the "date" fields, to parse it into separate elements
        prefixes = [key[:-5] for key in hyperdata.keys() if key[-5:] == "_date"]
        for prefix in prefixes:
            date = dateutil.parser.parse(hyperdata[prefix + "_date"])
            #print(date)

            hyperdata[prefix + "_year"]      = date.strftime("%Y")
            hyperdata[prefix + "_month"]     = date.strftime("%m")
            hyperdata[prefix + "_day"]       = date.strftime("%d")
            hyperdata[prefix + "_hour"]      = date.strftime("%H")
            hyperdata[prefix + "_minute"]    = date.strftime("%M")
            hyperdata[prefix + "_second"]    = date.strftime("%S")

        # finally, return the transformed result!
        return hyperdata
        print(hyperdata['publication_date'])

    def format_hyperdata_languages(self, hyperdata):
        """format the languages found in the hyperdata."""
        language = None
        language_keyerrors = {}
        for key in ('name', 'iso3', 'iso2', ):
            language_key = 'language_' + key
            if language_key in hyperdata:
                try:
                    language_symbol = hyperdata[language_key]
                    language = languages[language_symbol]
                    if language:
                        break
                except KeyError:
                    language_keyerrors[key] = language_symbol
        if language is not None:
            hyperdata['language_iso2'] = language.iso2
            hyperdata['language_iso3'] = language.iso3
            hyperdata['language_name'] = language.name
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
        """
        if file is None:
            file = self._file
        # if the file is a ZIP archive, recurse on each of its files...
        if zipfile.is_zipfile(file):
            zipArchive = zipfile.ZipFile(file)
            for filename in zipArchive.namelist():
                f = zipArchive.open(filename, 'r')
                yield from self.__iter__(f)
                f.close()
        # ...otherwise, let's parse it directly!
        else:
            try:
                file.seek(0)
            except:pass
            # debug: print(self.parse)  # do we have correct parser ?
            for hyperdata in self.parse(file):
                yield self.format_hyperdata(hyperdata)
