import networkx as nx
from networkx.readwrite import json_graph

print "hola"

G = nx.complete_graph(10)

f = open("testgraph.json","w")
f.write ( json_graph.dumps(G) )
f.close()
