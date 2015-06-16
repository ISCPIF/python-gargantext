
from django.template.loader import get_template
from django.template import Context
from django.contrib.auth.models import User, Group

from scrappers.scrap_pubmed.MedlineFetcherDavid2015 import MedlineFetcher

from urllib.request import urlopen, urlretrieve
import json

# from datetime import datetime
import time
import datetime
import os
import threading
from django.core.files import File
from gargantext_web.settings import DEBUG


from django.shortcuts import redirect
from django.shortcuts import render
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden

from sqlalchemy import func
from sqlalchemy.orm import aliased

from collections import defaultdict
import threading

from node.admin import CustomForm
from gargantext_web.db import *
from gargantext_web.settings import DEBUG, MEDIA_ROOT
from gargantext_web.api import JsonHttpResponse

from parsing.corpustools import add_resource, parse_resources, extract_ngrams, compute_tfidf

from gargantext_web.celery import apply_workflow
from time import sleep

from admin.utils import ensure_dir

def getGlobalStats(request ):
	print(request.method)
	alist = ["bar","foo"]

	if request.method == "POST":
		N = 1000
		query = request.POST["query"]
		print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" query =", query )
		print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" N =", N )
		instancia = MedlineFetcher()
		alist = instancia.serialFetcher( 5, query , N )

	data = alist
	return JsonHttpResponse(data)



def getGlobalStatsISTEXT(request ):
	print(request.method)
	alist = ["bar","foo"]

	if request.method == "POST":
		N = 1000
		query = request.POST["query"]
		print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" query =", query )
		print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" N =", N )
		query_string = query.replace(" ","+")
		url = "http://api.istex.fr/document/?q="+query_string

		tasks = MedlineFetcher()

		filename = MEDIA_ROOT + '/corpora/%s/%s' % (request.user, str(datetime.datetime.now().isoformat()))

		try: 
			thedata = tasks.test_downloadFile( [url,filename] )
			alist = thedata.read().decode('utf-8')
		except Exception as error:
			alist = [str(error)]
	data = alist
	return JsonHttpResponse(data)


def doTheQuery(request , project_id):
	alist = ["hola","mundo"]

	# do we have a valid project id?
	try:
		project_id = int(project_id)
	except ValueError:
		raise Http404()

	# do we have a valid project?
	project = (session
		.query(Node)
		.filter(Node.id == project_id)
		.filter(Node.type_id == cache.NodeType['Project'].id)
	).first()

	if project is None:
		raise Http404()

	# do we have a valid user?
	user = request.user
	if not user.is_authenticated():
		return redirect('/login/?next=%s' % request.path)
	if project.user_id != user.id:
		return HttpResponseForbidden()


	if request.method == "POST":
		query = request.POST["query"]
		name = request.POST["string"]

		instancia = MedlineFetcher()
		thequeries = json.loads(query)

		urlreqs = []
		for yearquery in thequeries:
			urlreqs.append( instancia.medlineEfetchRAW( yearquery ) )
		alist = ["tudo fixe" , "tudo bem"]

		resourcetype = cache.ResourceType["Pubmed (xml format)"]

		# corpus node instanciation as a Django model
		corpus = Node(
			name = name,
			user_id = request.user.id,
			parent_id = project_id,
			type_id = cache.NodeType['Corpus'].id,
			language_id = None,
                        hyperdata    = {'Processing' : 1,}
		)
		session.add(corpus)
		session.commit()

		# """
		# urlreqs: List of urls to query.
		# - Then, to each url in urlreqs you do:
		# 	eFetchResult = urlopen(url)
		# 	eFetchResult.read()  # this will output the XML... normally you write this to a XML-file.
		# """


		ensure_dir(request.user)
		tasks = MedlineFetcher()

		for i in range(8):
			t = threading.Thread(target=tasks.worker2) #thing to do
			t.daemon = True  # thread dies when main thread (only non-daemon thread) exits.
			t.start()
		for url in urlreqs:
			filename = MEDIA_ROOT + '/corpora/%s/%s' % (request.user, str(datetime.datetime.now().isoformat()))
			tasks.q.put( [url , filename]) #put a task in th queue
		tasks.q.join() # wait until everything is finished

		dwnldsOK = 0
		for filename in tasks.firstResults:
			if filename!=False:
				# add the uploaded resource to the corpus
				add_resource(corpus,
					user_id = request.user.id,
					type_id = resourcetype.id,
					file = filename,
				)
				dwnldsOK+=1
			
		if dwnldsOK == 0: return JsonHttpResponse(["fail"])

		try:
			if not DEBUG:
				apply_workflow.apply_async((corpus.id,),)
			else:
				thread = threading.Thread(target=apply_workflow, args=(corpus.id, ), daemon=True)
				thread.start()
		except Exception as error:
			print('WORKFLOW ERROR')
			print(error)
		sleep(1)
		return HttpResponseRedirect('/project/' + str(project_id))

	data = alist
	return JsonHttpResponse(data)


def testISTEX(request , project_id):
	print("testISTEX:")
	print(request.method)
	alist = ["bar","foo"]

	# do we have a valid project id?
	try:
		project_id = int(project_id)
	except ValueError:
		raise Http404()

	# do we have a valid project?
	project = (session
		.query(Node)
		.filter(Node.id == project_id)
		.filter(Node.type_id == cache.NodeType['Project'].id)
	).first()

	if project is None:
		raise Http404()

	# do we have a valid user?
	user = request.user
	if not user.is_authenticated():
		return redirect('/login/?next=%s' % request.path)
	if project.user_id != user.id:
		return HttpResponseForbidden()



	if request.method == "POST":
		# print(alist)
		query = "-"
		query_string = "-"
		N = 1000
		if "query" in request.POST: query = request.POST["query"]
		if "string" in request.POST: query_string = request.POST["string"].replace(" ","+")
		# if "N" in request.POST: N = request.POST["N"]
		print(query_string , query , N)


		urlreqs = []
		pagesize = 50
		tasks = MedlineFetcher()
		chunks = list(tasks.chunks(range(N), pagesize))
		for k in chunks:
			if (k[0]+pagesize)>N: pagesize = N-k[0]
			urlreqs.append("http://api.istex.fr/document/?q="+query_string+"&output=*&"+"from="+str(k[0])+"&size="+str(pagesize))


		resourcetype = cache.ResourceType["ISTex"]

		# corpus node instanciation as a Django model
		corpus = Node(
			name = query,
			user_id = request.user.id,
			parent_id = project_id,
			type_id = cache.NodeType['Corpus'].id,
			language_id = None, 
			hyperdata    = {'Processing' : 1,}
		)
		session.add(corpus)
		session.commit()


		ensure_dir(request.user)
		tasks = MedlineFetcher()

		for i in range(8):
			t = threading.Thread(target=tasks.worker2) #thing to do
			t.daemon = True  # thread dies when main thread (only non-daemon thread) exits.
			t.start()
		for url in urlreqs:
			filename = MEDIA_ROOT + '/corpora/%s/%s' % (request.user, str(datetime.datetime.now().isoformat()))
			tasks.q.put( [url , filename]) #put a task in th queue
		tasks.q.join() # wait until everything is finished

		dwnldsOK = 0
		for filename in tasks.firstResults:
			if filename!=False:
				# add the uploaded resource to the corpus
				add_resource(corpus,
					user_id = request.user.id,
					type_id = resourcetype.id,
					file = filename,
				)
				dwnldsOK+=1	
		if dwnldsOK == 0: return JsonHttpResponse(["fail"])		
		###########################
		###########################
		try:
			if not DEBUG:
				apply_workflow.apply_async((corpus.id,),)
			else:
				thread = threading.Thread(target=apply_workflow, args=(corpus.id, ), daemon=True)
				thread.start()
		except Exception as error:
			print('WORKFLOW ERROR')
			print(error)
		sleep(1)
		return HttpResponseRedirect('/project/' + str(project_id))


	data = [query_string,query,N]
	return JsonHttpResponse(data)

