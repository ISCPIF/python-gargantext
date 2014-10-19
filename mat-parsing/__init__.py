from Taggers import *
from NgramsExtractors import *
from FileParsers import *


import zipfile
import Collections
# import chardet


# This allows the fast retrieval of ngram ids
# from the cache instead of using the database
class Ngram_Cache:
    
    def __init__(self):
        self._cache = {}
            
    def get(self, terms):
        terms = terms.strip().lower()
        if terms not in self._cache:
            try:
                ngram = NGram.get(terms=terms)
            except:
                ngram = NGram(terms=terms, n=len(terms))
                ngram.save()
            self._cache[terms] = ngram.pk
        return self._cache[terms]



class Parser:

    def __init__(self):
        pass
    
    def parse_file(self, file):
        # CHECKER GUID!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        pass
        
    def parse_node(self, node):
        for resource in node.resources:
            if node.resources.file and zipfile.is_zipfile(node.resources.file):
                with zipfile.ZipFile(node.resources.file, "r") as zipFile:
                    for filename in zipFile.namelist():
                        file = zipFile.open(filename, "r")
                        node.add_child(
                            type = NodeType.get(name="Document"),
                            user = node.user,
                            
                        )
    
    def parse_node_recursively(self, node):
        self.parse_node(node)
        for descendant in node.get_descendants():
            self.parse_node(descendant)

