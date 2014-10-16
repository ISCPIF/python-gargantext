

"""Base class for all ngrams extractors.
"""
class NgramsExtractor:

    """Class instanciation.
    This method can be overriden.
    """
    def __init__(self):
        pass
    
    def tag_ngrams(self, contents):
        return []
    
    """Extracts a list of ngrams.
    Returns a list of the ngrams found in the given text.
    """
    def extract_ngrams(self, contents):
        tagged_ngrams = self.tag_ngrams()
        
        
    