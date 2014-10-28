from node.models import Node, NodeType, Language, Ngram, Node_Ngram
from parsing.NgramsExtractors import *

import collections
import dateutil.parser
import zipfile


class NgramCache:
    """This allows the fast retrieval of ngram ids
    from a cache instead of calling the database every time
    """
    
    def __init__(self, language):
        self._cache = dict()
        self._language = language
            
    def __getitem__(self, terms):
        terms = terms.strip().lower()
        if terms not in self._cache:
            try:
                ngram = Ngram.get(terms=terms, language=self._language)
            except:
                ngram = Ngram(terms=terms, n=len(terms.split()), language=self._language)
                ngram.save()
            self._cache[terms] = ngram
        return self._cache[terms]

        
class NgramCaches(collections.defaultdict):

    def __missing__(self, language):
        self[language] = NgramCache(language)
        return self[language]
        
    

class FileParser:
    """Base class for performing files parsing depending on their type.
    """
    
    def __init__(self, file=None, filepath="", encoding="utf8"):
        # ...get the file item...
        if file is None:
            self._file = open(filepath, "rb")
        else:
            self._file = file
        # cache for ngrams
        self._ngramcaches = NgramCaches()
        # extractors
        self._extractors = dict()
        self._document_nodetype = NodeType.objects.get(name='Document')
        languages = Language.objects.all()
        self._languages_fullname = {language.fullname.lower(): language for language in languages}
        self._languages_iso2 = {language.iso2.lower(): language for language in languages}
        self._languages_iso3 = {language.iso3.lower(): language for language in languages}
    
    def extract_ngrams(self, text, language):
        """Extract the ngrams from a given text.
        """
        # Get the appropriate ngrams extractor, if it exists
        if language not in self._extractors:
            extractor = None
            if language.iso2 == 'en':
                extractor = EnglishNgramsExtractor()
            elif language.iso2 == 'fr':
                extractor = FrenchNgramsExtractor()
            self._extractors[language] = extractor
        else:
            extractor = self._extractors[language]
        # Extract the ngrams
        if extractor:
            tokens = []
            for ngram in extractor.extract_ngrams(text):
                ngram_text = ' '.join([token for token, tag in ngram])
                tokens.append(ngram_text)
            return collections.Counter(tokens)
        else:
            return dict()
    
    def create_document(self, parentNode, title, metadata, guid=None):
        """Add a document to the database.
        """
        metadata = self.format_metadata(metadata)
        # create or retrieve a resource for that document, based on its user id
#        if guid is None:
#            resource = Resource(guid=guid)
#        else:
#            try:
#                resource = Resource.get(guid=guid)
#            except:
#                resource = Resource(guid=guid)
#        # If the parent node already has a child with this resource, pass
#        # (is it a good thing?)
#        if parentNode.descendants().filter(resource=resource).exists():
#            return None
        # create the document itself
        try:
            language = self._languages_iso3[metadata["language_iso3"]]
        except:
            language = None
        childNode = Node(
            user        = parentNode.user,
            type        = self._document_nodetype,
            name        = title,
            language    = language,
            metadata    = metadata,
            #resource    = resource,
            parent      = parentNode
        )
        childNode.save()
        return childNode
    
    
    def detect_encoding(self, string):
        """Useful method to detect the document encoding.
        """
        pass
    
    def _parse(self, parentNode, file):
        """This method shall be overriden by inherited classes."""
        return list()
        
    def parse(self, parentNode, file=None):
        """Parse the files found in the file.
        This method shall be overriden by inherited classes.
        """
        if file is None:
            with transaction.atomic():
                self.parse(parentNode, self._file)
        if zipfile.is_zipfile(file):
            with zipfile.ZipFile(file) as zipArchive:
                for filename in zipArchive.namelist():
                    self.parse(parentNode, zipArchive.open(filename, "r"))
        else:
            self._parse(parentNode, file)
    
    def extract(self, parentNode, keys):
       """Extract ngrams from the child nodes, given a list of field names."""
       # get all the descendants of type "document"
       childNodes = parentNode.descendants().filter(type=self._document_nodetype)
       with transaction.atomic():
           for childNode in childNodes:
                # most importantly...
                metadata = childNode.metadata
                # which extractor shall we use?
                if language not in self._extractors:
                    extractor = None
                    if language.iso2 == 'en':
                        # use English
                        extractor = EnglishNgramsExtractor()
                    elif language.iso2 == 'fr':
                        # use French
                        extractor = FrenchNgramsExtractor()
                    else:
                        # no recognized language has been specified...
                        continue
                    self._extractors[language] = extractor
                # extract ngrams from every field, find the id, count them
                ngrams = collections.defaultdict(int)
                ngramscache = self._ngramcaches[language]
                for key in keys:
                    for ngram in extractor.extract_ngrams(text):
                        ngram_text = ' '.join([token for token, tag in ngram])
                        ngram_id = ngramscache[ngramtext].id
                        ngrams[ngram_id] += 1
                # insert node/ngram associations in the database
                for ngram_id, occurences in ngrams.items():
                    Node_Ngram(
                        node_id    = childNode.id,
                        ngram_id   = ngram_id,
                        occurences = occurences
                    ).save()
    
    def format_metadata_dates(self, metadata):
        """Format the dates found in the metadata.
        Examples:
            {"publication_date": "2014-10-23 09:57:42"}
            -> {"publication_date": "2014-10-23 09:57:42", "publication_year": "2014"}
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
                
        # finally, return the result!
        return metadata
    def format_metadata_languages(self, metadata):
        """format the languages found in the metadata."""
        try:
            if "language_fullname" in metadata:
                language = self._languages_fullname[metadata["language_fullname"].lower()]
            elif "language_iso3" in metadata:
                language = self._languages_iso3[metadata["language_iso3"].lower()]
            elif "language_iso2" in metadata:
                language = self._languages_iso2[metadata["language_iso2"].lower()]
            else:
                return metadata
        except KeyError:
            # the language has not been found
            for key in ["language_fullname", "language_iso3", "language_iso2"]:
                try:
                    metadata.pop(key)
                except:
                    continue
            return metadata
        metadata["language_iso2"] = language.iso2
        metadata["language_iso3"] = language.iso3
        metadata["language_fullname"] = language.fullname
        return metadata
    def format_metadata(self, metadata):
        """Format the metadata."""
        metadata = self.format_metadata_dates(metadata)
        metadata = self.format_metadata_languages(metadata)
        return metadata
        
        
