import collections
import datetime
import dateutil.parser
import zipfile
import chardet
import re

from ..Caches import LanguagesCache


DEFAULT_DATE = datetime.datetime(datetime.MINYEAR, 1, 1)


class FileParser:
    """Base class for performing files parsing depending on their type.
    """
    def __init__(self, language_cache=None):
        self._languages_cache = LanguagesCache() if language_cache is None else language_cache

    def detect_encoding(self, string):
        """Useful method to detect the document encoding.
        """
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
            #date_string = re.sub(r'undefined', '', date_string)
            try:
                hyperdata['publication' + "_date"] = dateutil.parser.parse(
                    date_string,
                    default=DEFAULT_DATE
                ).strftime("%Y-%m-%d %H:%M:%S")
            except Exception as error:
                print(error, 'Parser Zotero, Date not parsed for:', date_string)
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
                except:
                    pass
        else:
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
        for key in ["fullname", "iso3", "iso2"]:
            language_key = "language_" + key
            if language_key in hyperdata:
                language_symbol = hyperdata[language_key]
                language = self._languages_cache[language_symbol]
                if language:
                    break
        if language:
            hyperdata["language_iso2"]       = language.iso2
            hyperdata["language_iso3"]       = language.iso3
            hyperdata["language_fullname"]   = language.fullname
        return hyperdata

    def format_hyperdata(self, hyperdata):
        """Format the hyperdata."""
        hyperdata = self.format_hyperdata_dates(hyperdata)
        hyperdata = self.format_hyperdata_languages(hyperdata)
        return hyperdata


    def _parse(self, file):
        """This method shall be overriden by inherited classes."""
        return list()

    def parse(self, file):
        """Parse the file, and its children files found in the file.
        """
        # initialize the list of hyperdata
        hyperdata_list = []
        # is the file is a ZIP archive, recurse on each of its files...
        if zipfile.is_zipfile(file):
            zipArchive = zipfile.ZipFile(file)
            for filename in zipArchive.namelist():
                try:
                    f = zipArchive.open(filename, 'r')
                    hyperdata_list += self.parse(f)
                    f.close()
                except Exception as error:
                    print(error)
        # ...otherwise, let's parse it directly!
        else:
            try:
                for hyperdata in self._parse(file):
                    hyperdata_list.append(self.format_hyperdata(hyperdata))
                if hasattr(file, 'close'):
                    file.close()
            except Exception as error:
                print(error)
        # return the list of formatted hyperdata
        return hyperdata_list


