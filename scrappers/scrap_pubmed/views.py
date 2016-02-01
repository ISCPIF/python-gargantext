
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
from gargantext_web.db import get_sessionmaker, session,get_session
from gargantext_web.settings import DEBUG, MEDIA_ROOT, BASE_DIR
from rest_v1_0.api import JsonHttpResponse

from parsing.corpustools import add_resource, parse_resources, extract_ngrams
from ngram.tfidf import compute_tfidf

from gargantext_web.celery import apply_workflow
from time import sleep

from admin.utils import ensure_dir

# pour lire la section [scrappers] de gargantext.ini
from configparser import ConfigParser
from os import path

# --------------------------------------------------------------------
# importing constants from config file
CONF = ConfigParser()
with open(path.join(BASE_DIR,'gargantext.ini')) as inifile:
	CONF.read_file(inifile)

QUERY_SIZE_N_MAX   = int(CONF['scrappers']['QUERY_SIZE_N_MAX'])

# QUERY_SIZE_N_DEFAULT   = int(CONF['scrappers']['QUERY_SIZE_N_DEFAULT'])
# --------------------------------------------------------------------
def getGlobalStats(request ):
	"""
	Pubmed year by year results

	# alist = [
	# {'string': '2011[dp] serendipity', 'queryKey': '1', 
	#  'webEnv': 'NCID_1_11...._F_1', 'count': 475, 'retmax': 6},
	# {'string': '2012[dp] serendipity', 'queryKey': '1', 
	#  'webEnv': 'NCID_1_14..._F_1', 'count': 345, 'retmax': 4},
	#  ... ]
	
	(reused as thequeries in doTheQuery)
	"""
	print(request.method)
	alist = []

	if request.method == "POST":
		query = request.POST["query"]
		N = int(request.POST["N"])
		
		if N > QUERY_SIZE_N_MAX:
			msg = "Invalid sample size N = %i (max = %i)" % (N, QUERY_SIZE_N_MAX)
			print("ERROR(scrap: pubmed stats): ",msg)
			raise ValueError(msg)
		
		print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" query =", query )
		print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" N =", N )
		instancia = MedlineFetcher()
		
		# serialFetcher (n_last_years, query, query_size)
		alist = instancia.serialFetcher( 5, query , N )

	data = alist
	return JsonHttpResponse(data)



def getGlobalStatsISTEXT(request ):
	"""
	ISTEX simply the total of hits for a query
	
	(not reused in testISTEX)
	"""
	print(request.method)
	alist = ["bar","foo"]

	if request.method == "POST":
		query = request.POST["query"]
		N = int(request.POST["N"])
		print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" query =", query )
		print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" N =", N )
		query_string = query.replace(" ","+")
		url = "http://api.istex.fr/document/?q="+query_string+"&output=id,title,abstract,pubdate,corpusName,authors,language"

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
	# implicit global session
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
		return redirect('/auth/?next=%s' % request.path)
	if project.user_id != user.id:
		return HttpResponseForbidden()


	if request.method == "POST":
		queries = request.POST["query"]
		name = request.POST["string"]
		
		# here we just realize queries already prepared by getGlobalStats
		#    ===> no need to repeat N parameter like in testISTEX <===
		
		instancia = MedlineFetcher()
		thequeries = json.loads(queries)
		
		# fyi the sum of our prepared yearly proportional quotas
		sampled_sum = sum([year_q['retmax'] for year_q in thequeries])
		print("Scrapping Pubmed: '%s' (N=%i)" % (name,sampled_sum))

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
                        hyperdata    = {'Processing' : "Parsing documents",}
		)
		session.add(corpus)
		session.commit()
		corpus_id = corpus.id
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
				apply_workflow.apply_async((corpus_id,),)
			else:
				thread = threading.Thread(target=apply_workflow, args=(corpus_id, ), daemon=True)
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
	# implicit global session
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
		return redirect('/auth/?next=%s' % request.path)
	if project.user_id != user.id:
		return HttpResponseForbidden()



	if request.method == "POST":
		query = "-"
		query_string = "-"
		N = 0
		
		if "query" in request.POST: 
			query = request.POST["query"]
			query_string = query.replace(" ","+")   # url encoded q

		if "N" in request.POST:
			N = int(request.POST["N"])     # query_size from views_opti
			if N > QUERY_SIZE_N_MAX:
				msg = "Invalid sample size N = %i (max = %i)" % (N, QUERY_SIZE_N_MAX)
				print("ERROR (scrap: istex d/l ): ",msg)
				raise ValueError(msg)

		print("Scrapping Istex: '%s' (%i)" % (query_string , N))

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
			hyperdata    = {'Processing' : "Parsing documents",}
		)
		session.add(corpus)
		session.commit()
		corpus_id = corpus.id
		
		print("NEW CORPUS", corpus_id)
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
				apply_workflow.apply_async((corpus_id,),)
			else:
				thread = threading.Thread(target=apply_workflow, args=(corpus_id, ), daemon=True)
				thread.start()
		except Exception as error:
			print('WORKFLOW ERROR')
			print(error)
		sleep(1)
		return HttpResponseRedirect('/project/' + str(project_id))


	data = [query_string,query,N]
	return JsonHttpResponse(data)
