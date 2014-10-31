
import parsing
from node.models import Node

node = Node.objects.get(name="PubMed corpus")

parser = parsing.Parser()

#parser.parse_node_fichier(node)
