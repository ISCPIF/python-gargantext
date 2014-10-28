import collections
from node.models import Ngram
from parsing.NgramsExtractors import EnglishNgramsExtractor, FrenchNgramsExtractor



class NgramsCache(collections.defaultdict):
    """This allows the fast retrieval of ngram ids
    from a cache instead of calling the database every time
    """
    
    def __init__(self, language):
        self.language = language
            
    def __missing__(self, terms):
        try:
            ngram = Ngram.get(terms=terms, language=self.language)
        except:
            ngram = Ngram(terms=terms, n=len(terms.split()), language=self.language)
            ngram.save()
        self[terms] = ngram
        return self[terms]
        
class NgramsCaches(collections.defaultdict):

    def __missing__(self, language):
        self[language] = NgramsCache(language)
        return self[language]
   
class NgramsExtractorsCache(collections.defaultdict):
    """This allows the fast retrieval of ngram ids
    from a cache instead of calling the database every time
    """
    
    def __missing__(self, key):
        # format the language
        if isinstance(key, str):
            language = key.strip().lower()
        else:
            language = key.iso3
        # find the proper extractor
        if language in ["en", "eng", "english"]:
            Extractor = EnglishNgramsExtractor
        elif language in ["fr", "fra", "fre", "french"]:
            Extractor = FrenchNgramsExtractor
        else:
            Extractor = NgramsExtractor
        # try to see if already instanciated, otherwise do it
        found = False
        for extractor in self.values():
            if type(extractor) == Extractor:
                self[key] = extractor
                found = True
                break
        if not found:
            self[key] = Extractor()
        # return the proper extractor
        return self[key]

   

class Cache:
    """This is THE cache of the caches."""
    def __init__(self):
        self.ngrams = NgramsCaches()
        self.extractors = NgramsExtractorsCache()
