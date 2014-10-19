import Collections

"""Base class for performing files parsing depending on their type.
"""
class FileParser:
    
    def __init__(self, file=None, filepath="", encoding="utf8"):
        # ...get the file item...
        if file is None:
            self._file = open(filepath, "rb")
        else:
            self._file = file
        # ...and parse!
        self.parse()
        # extractors
        self._extractors = {}
        self._document_nodetype = NodeType.get(label='document')
        with Language.objects.all() as languages:
            self._languages_iso2 = {language.iso2.lower(): language for language in Language}
            self._languages_iso3 = {language.iso3.lower(): language for language in Language}
    
    """Extract the ngrams from a given text.
    """
    def extract_ngrams(self, text, language):
        # Get the appropriate ngrams extractor, if it exists
        if language not in self._extractors:
            extractor = None
            if language == 'en':
                extractor = EnglishNgramsExtractor()
            elif language == 'fr':
                extractor = FrenchNgramsExtractor()
            self._extractors[language] = extractor
        else:
            extractor = self._extractors[language]
        # Extract the 
        if extractor:
            return extractor.extract_ngrams(text)
        else:
            return []
    
    """Add a document to the database.
    """
    def create_document(self, parentNode, title, contents, language, metadata, guid=None):
        # create or retrieve a resource for that document, based on its user id
        if guid is None:
            resource = Resource(guid=guid)
        else:
            try:
                resource = Resource.get(guid=guid)
            except:
                resource = Resource(guid=guid)
        # create the document itself
        childNode = Node(
            user        = parentNode.pk,
            type        = self._document_nodetype,
            name        = title,
            language    = language
            metadata    = metadata
            resource    = resource
        )
        parentNode.add_child(childNode)
        
        # parse it!
        ngrams = self.extract_ngrams(contents, language)
        for 
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
        pass