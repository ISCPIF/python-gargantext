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
    
    """Add a document to the database.
    """
    def create_document(self, title, contents, language, metadata, guid=None):
        # create or retrieve a resource for that document, based on its user id
        if guid is None:
            resource = Resource(guid=guid)
        else:
            try:
                resource = Resource.get(guid=guid)
            except:
                resource = Resource(guid=guid)
        # create the document itself
        document = Node(
            
            # WRITE STUFF HERE!!!
            
        )
        
        # parse it!
        # TODO: beware the language!!!!
        if self._parsers[language] = None:
            self._parsers[language] = NltkParser
        
        # WRITE STUFF HERE!!!
        
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