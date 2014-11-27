import collections
import dateutil.parser
import zipfile
import chardet

from parsing.Caches import LanguagesCache
    

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
    
    
    def format_metadata_dates(self, metadata):
        """Format the dates found in the metadata.
        Examples:
            {"publication_date": "2014-10-23 09:57:42"}
            -> {"publication_date": "2014-10-23 09:57:42", "publication_year": "2014", ...}
            {"publication_year": "2014"}
            -> {"publication_date": "2014-01-01 00:00:00", "publication_year": "2014", ...}
        """
        
        # First, check the split dates...
        prefixes = [key[:-5] for key in metadata.keys() if key[-5:] == "_year"]
        for prefix in prefixes:
            date_string = metadata[prefix + "_year"]
            key = prefix + "_month"
            if key in metadata:
                date_string += " " + metadata[key]
                key = prefix + "_day"
                if key in metadata:
                    date_string += " " + metadata[key]
                    key = prefix + "_hour"
                    if key in metadata:
                        date_string += " " + metadata[key]
                        key = prefix + "_minute"
                        if key in metadata:
                            date_string += ":" + metadata[key]
                            key = prefix + "_second"
                            if key in metadata:
                                date_string += ":" + metadata[key]
            try:
                metadata[prefix + "_date"] = dateutil.parser.parse(date_string).strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
        
        # ...then parse all the "date" fields, to parse it into separate elements
        prefixes = [key[:-5] for key in metadata.keys() if key[-5:] == "_date"]
        for prefix in prefixes:
            date = dateutil.parser.parse(metadata[prefix + "_date"])
            metadata[prefix + "_year"]      = date.strftime("%Y")
            metadata[prefix + "_month"]     = date.strftime("%m")
            metadata[prefix + "_day"]       = date.strftime("%d")
            metadata[prefix + "_hour"]      = date.strftime("%H")
            metadata[prefix + "_minute"]    = date.strftime("%M")
            metadata[prefix + "_second"]    = date.strftime("%S")
                
        # finally, return the transformed result!
        return metadata
        
    def format_metadata_languages(self, metadata):
        """format the languages found in the metadata."""
        language = None
        for key in ["fullname", "iso3", "iso2"]:
            language_key = "language_" + key
            if language_key in metadata:
                language_symbol = metadata[language_key]
                language = self._languages_cache[language_symbol]
                if language:
                    break
        if language:
            metadata["language_iso2"] = language.iso2
            metadata["language_iso3"] = language.iso3
            metadata["language_fullname"] = language.fullname
        return metadata
        
    def format_metadata(self, metadata):
        """Format the metadata."""
        metadata = self.format_metadata_dates(metadata)
        metadata = self.format_metadata_languages(metadata)
        return metadata
    
    
    def _parse(self, file):
        """This method shall be overriden by inherited classes."""
        return list()
        
    def parse(self, file):
        """Parse the file, and its children files found in the file.
        """
        # initialize the list of metadata
        metadata_list = []
        # is the file is a ZIP archive, recurse on each of its files...
        if zipfile.is_zipfile(file):
            zipArchive = zipfile.ZipFile(file)
            for filename in zipArchive.namelist():
                metadata_list += self.parse(zipArchive.open(filename, "r"))
        # ...otherwise, let's parse it directly!
        else:
            metadata_list += self._parse(file)
        # return the list of formatted metadata
        return map(self.format_metadata, metadata_list)

