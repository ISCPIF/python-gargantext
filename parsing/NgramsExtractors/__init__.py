from parsing.NgramsExtractors.FrenchNgramsExtractor import FrenchNgramsExtractor
from parsing.NgramsExtractors.EnglishNgramsExtractor import EnglishNgramsExtractor
from parsing.NgramsExtractors.NgramsExtractor import NgramsExtractor

import collections


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

