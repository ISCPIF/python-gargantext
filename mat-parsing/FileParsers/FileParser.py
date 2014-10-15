import Collections

"""Base class for performing files parsing depending on their type.
"""
class FileParser:
    
    def __init__(self, file=None, path="", encoding="utf8"):
        # ...get the file item...
        if file is None:
            self._file = open(path, "rb")
        else:
            self._file = file
        # ...and parse!
        self.parse()
    
    """Add a document to the database.
    """
    def add_document(self, parent, title, contents, metadata, resource_guid=None):
        # create or retrieve a resource for that document, based on its user id
        if resource_guid is None:
            resource = Resource(guid=resource_guid)
        else:
            try:
                resource = Resource.get(guid=resource_guid)
            except:
                resource = Resource(guid=resource_guid)
        # create the document itself
        document = 
    
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