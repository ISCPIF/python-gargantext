#from .Taggers import *
#from .NgramsExtractors import *
from .FileParsers import *
from node.models import Node, NodeType

import zipfile
import collections
# import chardet



class Parser:

    def __init__(self):
        pass
    
    def parse_file(self, file):
        # CHECKER GUID!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        pass
        
    def parse_node_fichier(self, node):
        if node.fichier and zipfile.is_zipfile(node.fichier):
            with zipfile.ZipFile(node.fichier, "r") as zipFile:
                node_type = NodeType.objects.get(name="Document")
                for filename in zipFile.namelist():
                    file = zipFile.open(filename, "r")
                    node.objects.create(
                        parent = node,
                        type = node_type,
                        user = node.user,
                    )
    
    def parse_node(self, node):
        for resource in node.resources:
            if node.resources.file and zipfile.is_zipfile(node.resources.file):
                with zipfile.ZipFile(node.resources.file, "r") as zipFile:
                    for filename in zipFile.namelist():
                        file = zipFile.open(filename, "r")
                        Node.objects.create(
                            parent = node,
                            type = NodeType.get(name="Document"),
                            user = node.user,
                            
                        )
    
    def parse_node_recursively(self, node):
        self.parse_node(node)
        for descendant in node.get_descendants():
            self.parse_node(descendant)

