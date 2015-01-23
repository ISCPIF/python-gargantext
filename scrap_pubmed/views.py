from django.shortcuts import redirect
from django.shortcuts import render

from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.template.loader import get_template
from django.template import Context

from scrap_pubmed.MedlineFetcherDavid2015 import MedlineFetcher

from gargantext_web.api import JsonHttpResponse
# Create your views here.

def getGlobalStats(request ):
	print(request.method)
	alist = ["bar","foo"]

	if request.method == "POST":
		query = request.POST["query"]
		instancia = MedlineFetcher()
		alist = instancia.serialFetcher( 5, query , 200 )

	data = alist
	return JsonHttpResponse(data)


def doTheQuery(request ):
	print(request.method)
	alist = ["hola","mundo"]

	if request.method == "POST":
		query = request.POST
		print(query)

	data = alist
	return JsonHttpResponse(data)