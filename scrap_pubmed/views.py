from django.shortcuts import redirect
from django.shortcuts import render

from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.template.loader import get_template
from django.template import Context

from scrap_pubmed.MedlineFetcherDavid2015 import MedlineFetcher

from gargantext_web.api import JsonHttpResponse
import json

from node.models import Language, ResourceType, Resource, \
        Node, NodeType, Node_Resource, Project, Corpus, \
        Ngram, Node_Ngram, NodeNgramNgram, NodeNodeNgram


def getGlobalStats(request ):
	print(request.method)
	alist = ["bar","foo"]

	if request.method == "POST":
		query = request.POST["query"]
		instancia = MedlineFetcher()
		alist = instancia.serialFetcher( 5, query , 200 )

	data = alist
	return JsonHttpResponse(data)


def doTheQuery(request , project_id):
	alist = ["hola","mundo"]

	if request.method == "POST":
		query = request.POST["query"]
		name = request.POST["string"]

		instancia = MedlineFetcher()
		thequeries = json.loads(query)

		print("------------------")

		urlreqs = []
		for yearquery in thequeries:
			print("fetching:")
			print(yearquery)
			urlreqs.append( instancia.medlineEfetchRAW( yearquery ) )
			print(" - - - - - ")
		print( "============================" )
		print(urlreqs)
		alist = ["tudo fixe" , "tudo bem"]

		"""
		urlreqs: List of urls to query.
		- Then, to each url in urlreqs you do:
			eFetchResult = urlopen(url)
			eFetchResult.read()  # this will output the XML... normally you write this to a XML-file.
		"""
		# print("finding out project ID:")
		# print(project_id)

		# thefile = "how we do this here?"
		# resource_type = ResourceType()
		# resource_type.name = name

		# print("-------------")
		# print(name,"|",resource_type,"|",thefile)
		# print("-------------")

		# print(request.user)

		# try:
		# 	parent      = Node.objects.get(id=project_id)
		# 	print("IMMA    HEEEEERE 01")
		# 	node_type   = NodeType.objects.get(name='Corpus')
		# 	print("IMMA    HEEEEERE 02")

		# 	corpus = Node(
		# 		user=request.user,
		# 		parent=parent,
		# 		type=node_type,
		# 		name=name,
		# 	)

		# 	print("IMMA    HEEEEERE 03")
		# 	corpus.save()

		# 	print("IMMA    HEEEEERE 04")
		# 	corpus.add_resource(
		# 		user=request.user,
		# 		type=resource_type,
		# 		file=urlreqs
		# 	)
		# 	print("IMMA    HEEEEERE 05")


		# except Exception as error:
		# 	print(error)




	data = alist
	return JsonHttpResponse(data)