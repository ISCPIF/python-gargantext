import collections
from node.models import Ngram
from parsing.NgramsExtractors import EnglishNgramsExtractor, FrenchNgramsExtractor



class NgramsCache(collections.defaultdict):
    """This allows the fast retrieval of ngram ids
    from a cache instead of calling the database every time.
    This class is language-specific."""    
    def __init__(self, language):
        """The cache only works with one language,
        which is the required parameter of the constructor."""
        self.language = language
            
    def __missing__(self, terms):
        """If the terms are not yet present in the dictionary,
        retrieve it from the database or insert it."""
        try:
            ngram = Ngram.get(terms=terms, language=self.language)
        except:
            ngram = Ngram(terms=terms, n=len(terms.split()), language=self.language)
            ngram.save()
        self[terms] = ngram
        return self[terms]
        
class NgramsCaches(collections.defaultdict):
    """This allows the fast retrieval of ngram ids
    from a cache instead of calling the database every time."""
    def __missing__(self, language):
        """If the cache for this language is not reachable,
        add id to the dictionary."""
        self[language] = NgramsCache(language)
        return self[language]
   
class NgramsExtractorsCache(collections.defaultdict):
    """This allows the fast retrieval of ngram ids
    from a cache instead of calling the database every time."""    
    def __missing__(self, key):
        """If the ngrams extractor is not instancianted yet
        for the given language, do it!"""
        # format the language
        if isinstance(key, str):
            language = key.strip().lower()
        else:
            language = key.iso2
        # find the proper extractor
        if language in ["en", "eng", "english"]:
            Extractor = EnglishNgramsExtractor
        elif language in ["fr", "fra", "fre", "french"]:
            Extractor = FrenchNgramsExtractor
        else:
            Extractor = NgramsExtractor
        # try to see if already instanciated with another key
        found = False
        for extractor in self.values():
            if type(extractor) == Extractor:
                self[key] = extractor
                found = True
                break
        # well if not, let's instanciate it...
        if not found:
            self[key] = Extractor()
        # return the proper extractor
        return self[key]

   

class Cache:
    """This is THE cache of the caches.
    See NgramsCaches and NgramsExtractorsCache for better understanding."""
    def __init__(self):
        self.ngrams = NgramsCaches()
        self.extractors = NgramsExtractorsCache()
