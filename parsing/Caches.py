

class NgramsCache:
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

        
class NgramsCaches(collections.defaultdict):

    def __missing__(self, language):
        self[language] = NgramsCache(language)
        return self[language]
        

class Cache:
    
    def __init__(self):
        self.ngrams_caches = NgramsCaches()
        self.