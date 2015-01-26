from django.shortcuts import redirect
from django.shortcuts import render

from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.template.loader import get_template
from django.template import Context
from django.contrib.auth.models import User

from scrap_pubmed.MedlineFetcherDavid2015 import MedlineFetcher

from gargantext_web.api import JsonHttpResponse
from urllib.request import urlopen, urlretrieve
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


from parsing.FileParsers import PubmedFileParser
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
			urlreqs.append( instancia.medlineEfetchRAW( yearquery ) )
		alist = ["tudo fixe" , "tudo bem"]

		"""
		urlreqs: List of urls to query.
		- Then, to each url in urlreqs you do:
			eFetchResult = urlopen(url)
			eFetchResult.read()  # this will output the XML... normally you write this to a XML-file.
		"""

		thefile = "how we do this here?"
		resource_type = ResourceType()
		resource_type.name = name

		try:
			parent      = Node.objects.get(id=project_id)
			node_type   = NodeType.objects.get(name='Corpus')
			type_id = NodeType.objects.get(name='Document').id
			user_id = User.objects.get( username=request.user ).id

			corpus = Node(
				user=request.user,
				parent=parent,
				type=node_type,
				name=name,
			)

			corpus.save()
			
			parser = PubmedFileParser()
			metadata_list = []
			for url in urlreqs:
				data = urlopen(url)
				metadata_list += parser.parse( data.read() )
				# corpus.add_resource( user=request.user, type=resource_type, file=data.read() )
				break


			from parsing.Caches import LanguagesCache
			langages_cache = LanguagesCache()
			for i, metadata_values in enumerate(metadata_list):
				name = metadata_values.get('title', '')[:200]
				language = langages_cache[metadata_values['language_iso2']] if 'language_iso2' in metadata_values else None,
				if isinstance(language, tuple):
					language = language[0]

				Node(
					user_id  = user_id,
					type_id  = type_id,
					name     = name,
					parent   = parent,
					language_id = language.id if language else None,
					metadata = metadata_values
				).save()

			parent.children.all().make_metadata_filterable()

			type_document   = NodeType.objects.get(name='Document')
			print("printing here 01")
			parent.children.filter(type_id=type_document.pk).extract_ngrams(keys=['title',])
			print("printing here 02")

			print("now we've to apply do_tfidf...")


			# thetitles = parent.children.filter(type_id=type_document.pk)
			# print(Node.objects.filter(parent=parent))
			# from analysis.functions import do_tfidf
			# do_tfidf(corpus)

			print("ca va?")

		except Exception as error:
			print("lele",error)



	data = alist
	return JsonHttpResponse(data)