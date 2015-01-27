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

from gargantext_web.settings import MEDIA_ROOT
from datetime import datetime
from django.core.files import File
from gargantext_web.settings import DEBUG

from node.models import Language, ResourceType, Resource, \
        Node, NodeType, Node_Resource, Project, Corpus, \
        Ngram, Node_Ngram, NodeNgramNgram, NodeNodeNgram


def getGlobalStats(request ):
	print(request.method)
	alist = ["bar","foo"]

	if request.method == "POST":
		query = request.POST["query"]
		instancia = MedlineFetcher()
		alist = instancia.serialFetcher( 5, query , 100 )

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
		resource_type = ResourceType.objects.get(name="pubmed" )

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

		try:
			for url in urlreqs:
				print(url)
				data = urlopen(url)
				xmlname = MEDIA_ROOT + '/corpora/%s/%s.xml' % (request.user, str(datetime.now().microsecond))
				f = open(xmlname, 'w')
				myfile = File(f)
				myfile.write( data.read().decode('utf-8') )
				myfile.close()
				f.close()
				corpus.add_resource( user=request.user, type=resource_type, file=xmlname )

			try:
				if DEBUG is True:
					corpus.workflow()
				else:
					corpus.workflow.apply_async((), countdown=3)

				return JsonHttpResponse(["workflow","finished"])

			except Exception as error:
				print(error)

			return JsonHttpResponse(["workflow","finished","outside the try-except"])

		except Exception as error:
			print("lele",error)

	data = alist
	return JsonHttpResponse(data)