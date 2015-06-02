import networkx as nx
from itertools import combinations

class Utils:

	def __init__(self):
		self.G = nx.Graph()

	def unique(self,a):
		""" return the list with duplicate elements removed """
		return list(set(a))

	def intersect(self,a, b):
		""" return the intersection of two lists """
		return list(set(a) & set(b))

	def union(self,a, b):
		""" return the union of two lists """
		return list(set(a) | set(b))

	def addCompleteSubGraph(self,terms):
		G=self.G
		# <addnode> #
		for i in terms:
			G.add_node(i)
		# </addnode> #

		# <addedge> #
		edges = combinations(terms, 2)
		for n in edges:
			n1=n[0]
			n2=n[1]
			one=float(1)
			if G.has_edge(n1,n2):
				G[n1][n2]['weight']+=one
			else: G.add_edge(n1,n2,weight=one)
		self.G = G