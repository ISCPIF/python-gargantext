import collections
from node.models import Node, NodeType, Language

class NgramCache:
    """
    This allows the fast retrieval of ngram ids
    from the cache instead of using the database for every call
    """
    
    def __init__(self, language):
        self._cache = dict()
        self._language = language
            
    def __getitem__(self, terms):
        terms = terms.strip().lower()
        if terms not in self._cache:
            try:
                ngram = NGram.get(terms=terms, language=self._language)
            except:
                ngram = NGram(terms=terms, n=len(terms), language=self._language)
                ngram.save()
            self._cache[terms] = ngram
        return self._cache[terms]

        
class NgramCaches(collections.defaultdict):

    def __missing__(self, language):
        self[language] = NgramCache(language)
        return self[language]
        
    

"""Base class for performing files parsing depending on their type.
"""
class FileParser:
    
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
        self._languages_iso2 = {language.iso2.lower(): language for language in languages}
        self._languages_iso3 = {language.iso3.lower(): language for language in languages}
        #self.parse()
    
    """Extract the ngrams from a given text.
    """
    def extract_ngrams(self, text, language):
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
            return collections.Counter(
                [token for token, tag in extractor.extract_ngrams(text)]
            )
        else:
            return dict()
    
#TODO
#   * make it possible to tag and parse separately
#   * only tags some data (only titles, titles & abstracts, some chapters...)

    """Add a document to the database.
    """
    def create_document(self, parentNode, title, contents, language, metadata, guid=None):
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
        childNode = Node(
            user        = parentNode.pk,
            type        = self._document_nodetype,
            name        = title,
            language    = language,
            metadata    = metadata,
            #resource    = resource,
            parent      = parentNode
        )
            
        # parse it!
        ngrams = self.extract_ngrams(contents, language)
        # we are already in a transaction, so no use doing another one (or is there?)
        ngramcache = self._ngramcaches[language]
        for terms, occurences in ngrams.items():
            ngram_text = ' '.join([term[0] for term in terms])
            ngram = ngramcache[ngram_text]
            Node_Ngram(
                node       = childNode,
                ngram      = ngram,
                occurences = occurences
            ).save()
                
        # return the created document
        return document
    
    """Useful method to detect the document encoding.
    Not sure it should be here actually.
    """
    def detect_encoding(self, string):
        # see the chardet library
        pass
    
    """Parse the data.
    This method shall be overriden by inherited classes.
    """
    def parse(self):
        return list()

