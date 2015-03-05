from django.db import models
from django.utils import timezone

from django.contrib.auth.models import User

from django_hstore import hstore
from cte_tree.models import CTENode, CTENodeManager
# from cte_tree.query import CTEQuerySet
#from cte_tree.fields import DepthField, PathField, OrderingField

from parsing.Caches import LanguagesCache, NgramsExtractorsCache, NgramsCaches
from parsing.FileParsers import *

from time import time
import datetime
from multiprocessing import Process
from math import log

from collections import defaultdict
import hashlib

from gargantext_web.settings import MEDIA_ROOT

from celery.contrib.methods import task_method
from celery import current_app

import os
import subprocess


# Some usefull functions
# TODO: start the function name with an underscore (private)
def _upload_to(instance, filename):
    return MEDIA_ROOT + '/corpora/%s/%s' % (instance.user.username, filename)

# All classes here

class Language(models.Model):
    iso2        = models.CharField(max_length=2, unique=True)
    iso3        = models.CharField(max_length=3, unique=True)
    fullname    = models.CharField(max_length=255, unique=True)
    implemented = models.BooleanField(blank=True)
    
    def __str__(self):
        return self.fullname

class ResourceType(models.Model):
    name    = models.CharField(max_length=255, unique=True)
    
    def __str__(self):
        return self.name

class Ngram(models.Model):
    language    = models.ForeignKey(Language, blank=True, null=True, on_delete=models.SET_NULL)
    n           = models.IntegerField()
    terms       = models.CharField(max_length=255, unique=True)
    nodes       = models.ManyToManyField(through='Node_Ngram', to='Node')
    
    def __str__(self):
        return self.terms


class Resource(models.Model):
    user        = models.ForeignKey(User)
    guid        = models.CharField(max_length=255)
    type        = models.ForeignKey(ResourceType, blank=True, null=True)
    file        = models.FileField(upload_to=_upload_to, blank=True)
    digest      = models.CharField(max_length=32) # MD5 digest
    def __str__(self):
        return self.file

class NodeType(models.Model):
    name        = models.CharField(max_length=200, unique=True)
    def __str__(self):
        return self.name

class NodeQuerySet(CTENodeManager.CTEQuerySet):
    """Methods available from Node querysets."""
    def extract_ngrams(self, keys, ngramsextractorscache=None, ngramscaches=None):
        if ngramsextractorscache is None:
            ngramsextractorscache = NgramsExtractorsCache()
        if ngramscaches is None:
            ngramscaches = NgramsCaches()
        for node in self:
            node.extract_ngrams(keys, ngramsextractorscache, ngramscaches)

    def make_metadata_filterable(self):
        metadata_cache = {metadata.name: metadata for metadata in Metadata.objects.all()}
        data = []
        for node in self:
            for key, value in node.metadata.items():
                if key in metadata_cache:
                    metadata = metadata_cache[key]
                    if metadata.type == 'string':
                        value = value[:255]
                    data.append(Node_Metadata(**{
                        'node_id' : node.id,
                        'metadata_id' : metadata.id,
                        ('value_'+metadata.type) : value,
                    }))
        Node_Metadata.objects.bulk_create(data)
    
class NodeManager(CTENodeManager):
    """Methods available from Node.object."""
    def get_queryset(self):
        self._ensure_parameters()
        return NodeQuerySet(self.model, using=self._db)
    def __getattr__(self, name, *args):
        if name.startswith("_"): 
            raise AttributeError
        return getattr(self.get_queryset(), name, *args)

class Metadata(models.Model):
    name        = models.CharField(max_length=32, db_index=True)
    type        = models.CharField(max_length=16, db_index=True)
        
class Node(CTENode):
    """The node."""
    objects     = NodeManager()

    user        = models.ForeignKey(User)
    type        = models.ForeignKey(NodeType)
    name        = models.CharField(max_length=200)
    
    language    = models.ForeignKey(Language, blank=True, null=True, on_delete=models.SET_NULL)
    
    date        = models.DateField(default=timezone.now, blank=True)
    metadata    = hstore.DictionaryField(blank=True)

    ngrams      = models.ManyToManyField(through='Node_Ngram', to='Ngram')

    def __str__(self):
        return self.name
    
    def get_resources(self):
        return Resource.objects.select_related('node_resource').filter(node_resource__node = self)

    def add_resource(self, **kwargs):
        # only for tests
        resource = Resource(guid=str(time()), digest=str(time()), **kwargs )
        #resource = Resource(**kwargs)
        resource.save()

        # User
        if 'user' not in kwargs and 'user_id' not in kwargs:
            resource.user = self.user
        # Compute the digest
        h = hashlib.md5()
        f = open(str(resource.file), 'rb')
        h.update(f.read())
        f.close()
        resource.digest = h.hexdigest()
        # check if a resource on this node already has this hash
        tmp_resource = self.get_resources().filter(digest = resource.digest).first()
        if tmp_resource:
            return tmp_resource
        else:
            resource.save()
        # link with the resource
        node_resource = Node_Resource(
            node     = self,
            resource = resource
        )
        node_resource.save()
        return resource
    
    def parse_resources(self, verbose=False):
        # parse all resources into a list of metadata
        metadata_list = []
        print("not parsed resources:")
        print(self.node_resource.filter(parsed=False))
        print("= = = = = = = = =  = =\n")
        for node_resource in self.node_resource.filter(parsed=False):
            resource = node_resource.resource
            parser = defaultdict(lambda:FileParser.FileParser, {
                'istext'    : ISText,
                'pubmed'    : PubmedFileParser,
                'isi'       : IsiFileParser,
                'ris'       : RisFileParser,
                'europress' : EuropressFileParser,
                'europress_french'  : EuropressFileParser,
                'europress_english' : EuropressFileParser,
            })[resource.type.name]()
            metadata_list += parser.parse(str(resource.file))
        type_id = NodeType.objects.get(name='Document').id
        langages_cache = LanguagesCache()
        user_id = self.user.id
        # insert the new resources in the database!
        for i, metadata_values in enumerate(metadata_list):
            if verbose:
                print(i, end='\r', flush=True)
            name = metadata_values.get('title', '')[:200]
            language = langages_cache[metadata_values['language_iso2']] if 'language_iso2' in metadata_values else None,
            if isinstance(language, tuple):
                language = language[0]
            # print("metadata_values:")
            # print("\t",metadata_values,"\n- - - - - - - - - - - - ")
            Node(
                user_id  = user_id,
                type_id  = type_id,
                name     = name,
                parent   = self,
                language_id = language.id if language else None,
                metadata = metadata_values
            ).save()
        # make metadata filterable
        self.children.all().make_metadata_filterable()

        # mark the resources as parsed for this node
        self.node_resource.update(parsed=True)

    @current_app.task(filter=task_method)
    def extract_ngrams(self, keys, ngramsextractorscache=None, ngramscaches=None):
        # if there is no cache...
        if ngramsextractorscache is None:
            ngramsextractorscache = NgramsExtractorsCache()
        if ngramscaches is None:
            ngramscaches = NgramsCaches()
        # what do we want from the cache?
        language = self.language if self.language else self.parent.language
        #print(language.fullname)
        extractor = ngramsextractorscache[language]
        ngrams = ngramscaches[language]
        # find & count all the occurrences
        associations = defaultdict(float) # float or int?
        if isinstance(keys, dict):
            for key, weight in keys.items():
                text2process = str(self.metadata[key]).replace('[','').replace(']','')
                for ngram in extractor.extract_ngrams(text2process):
                    terms = ' '.join([token for token, tag in ngram])
                    associations[ngram] += weight
        else:
            for key in keys:
                text2process = str(self.metadata[key]).replace('[','').replace(']','')
                for ngram in extractor.extract_ngrams(text2process):
                    terms = ' '.join([token for token, tag in ngram])
                    associations[terms] += 1
        Node_Ngram.objects.bulk_create([
            Node_Ngram(
                node   = self,
                ngram  = ngrams[ngram_text],
                weight = weight
            )
            for ngram_text, weight in associations.items()
        ])

    @current_app.task(filter=task_method)
    def workflow(self, keys=None, ngramsextractorscache=None, ngramscaches=None, verbose=False):
        import time
        total = 0
        print("LOG::TIME: In workflow()    parse_resources()")
        start = time.time()
        self.metadata['Processing'] = 1
        self.save()
        self.parse_resources()
        end = time.time()
        total += (end - start)
        print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" parse_resources() [s]",(end - start))
        print("LOG::TIME: In workflow()    / parse_resources()")

        start = time.time()
        print("LOG::TIME: In workflow()    extract_ngrams()")
        print("\n- - - - - - - - - -")
        type_document   = NodeType.objects.get(name='Document')
        self.children.filter(type_id=type_document.pk).extract_ngrams(keys=['title',])
        end = time.time()
        print("- - - - - - - - - - \n")
        total += (end - start)
        print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" extract_ngrams() [s]",(end - start))
        print("LOG::TIME: In workflow()    / extract_ngrams()")
        
        start = time.time()
        print("In workflow()    do_tfidf()")
        from analysis.functions import do_tfidf
        do_tfidf(self)
        end = time.time()
        total += (end - start)
        print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" do_tfidf() [s]",(end - start))
        print("LOG::TIME: In workflow()    / do_tfidf()")
        print("In workflow() END")
        self.metadata['Processing'] = 0
        self.save()

    def runInParallel(self, *fns):
        proc = []
        for fn in fns:
            p = Process(target=fn)
            p.start()
            proc.append(p)
        for p in proc:
            p.join()

    def parse_resources__MOV(self, verbose=False):
        # parse all resources into a list of metadata
        metadata_list = []
        print("not parsed resources:")
        print(self.node_resource.filter(parsed=False))
        print("= = = = = = = = =  = =\n")
        for node_resource in self.node_resource.filter(parsed=False):
            resource = node_resource.resource
            parser = defaultdict(lambda:FileParser.FileParser, {
                'istext'    : ISText,
                'pubmed'    : PubmedFileParser,
                'isi'       : IsiFileParser,
                'ris'       : RisFileParser,
                'europress' : EuropressFileParser,
                'europress_french'  : EuropressFileParser,
                'europress_english' : EuropressFileParser,
            })[resource.type.name]()
            metadata_list += parser.parse(str(resource.file))
        self.node_resource.update(parsed=True) #writing to DB
        return metadata_list

    def writeMetadata__MOV(self, metadata_list=None , verbose=False):
        type_id = NodeType.objects.get(name='Document').id
        user_id = self.user.id
        langages_cache = LanguagesCache()
        # # insert the new resources in the database!
        for i, metadata_values in enumerate(metadata_list):
            name = metadata_values.get('title', '')[:200]
            language = langages_cache[metadata_values['language_iso2']] if 'language_iso2' in metadata_values else None,
            if isinstance(language, tuple):
                language = language[0]
            node = Node(
                user_id  = user_id,
                type_id  = type_id,
                name     = name,
                parent   = self,
                language_id = language.id if language else None,
                metadata = metadata_values
            )
            node.save()
            metadata_values["id"] = node.id
        # # make metadata filterable
        self.children.all().make_metadata_filterable()
        # # mark the resources as parsed for this node
        self.node_resource.update(parsed=True)
        return metadata_list

    def extract_ngrams__MOV(self, array , keys , ngramsextractorscache=None, ngramscaches=None):
        if ngramsextractorscache is None:
            ngramsextractorscache = NgramsExtractorsCache()
        langages_cache = LanguagesCache()

        if ngramscaches is None:
            ngramscaches = NgramsCaches()

        results = []
        i = 0
        for metadata in array:
            associations = defaultdict(float) # float or int?
            language = langages_cache[metadata['language_iso2']] if 'language_iso2' in metadata else None,
            if isinstance(language, tuple):
                language = language[0]

            extractor = ngramsextractorscache[language]
            ngrams = ngramscaches[language]
            # theText = []

            if isinstance(keys, dict):
                for key, weight in keys.items():
                    if key in metadata:
                        text2process = str(metadata[key]).replace('[','').replace(']','')
                        # theText.append(text2process)
                        for ngram in extractor.extract_ngrams(text2process):
                            terms = ' '.join([token for token, tag in ngram]).strip().lower()
                            associations[ngram] += weight
            else:
                for key in keys:
                    if key in metadata:
                        text2process = str(metadata[key]).replace('[','').replace(']','')
                        # theText.append(text2process)
                        for ngram in extractor.extract_ngrams(text2process):
                            terms = ' '.join([token for token, tag in ngram]).strip().lower()
                            associations[terms] += 1

            if(len(associations)>0):
                results.append( [metadata["id"] , associations] )
            
            i+=1
        return results
    
    def do_tfidf__MOV( self, FreqList , Metadata , n=150):

        from analysis.InterUnion import Utils
        calc = Utils()

        # *01* [ calculating global count of each ngram ]
        GlobalCount = {}
        for i in FreqList:
            docID = i[0]
            associations = i[1]
            for ngram_text, weight in associations.items():
                if len(ngram_text.split())>1 and len(ngram_text.split())<4:# considering just {2,3}-grams
                    if ngram_text in GlobalCount: 
                        if "C" in GlobalCount[ngram_text]:
                            GlobalCount[ngram_text]["C"] += 1
                        else: 
                            GlobalCount[ngram_text] = {}
                            GlobalCount[ngram_text]["C"] = 1
                    else:
                        GlobalCount[ngram_text] = {}
                        GlobalCount[ngram_text]["C"] = 1
        # *01* [ / calculating global count of each ngram ]
        

        # *02* [ Considering the first <150 ngrams by DESC occurrences ]
        FirstNgrams = {}
        sortedList = sorted(GlobalCount, key=lambda x: GlobalCount[x]['C'], reverse=True)
        for i in range(len(sortedList)):
            term = sortedList[i]
            FirstNgrams[term] = {}
            FirstNgrams[term]["C"] = GlobalCount[term]["C"]
            if i==(n-1): break
        # *02* [ / Considering the first <150 ngrams by DESC occurrences ]

        N = float(len(FreqList)) #nro docs really processed


        # *03* [ making dictionaries  for  NGram_Text <=> NGram_ID ]
        NGram2ID = {}
        ID2NGram = {}
        ngramid = 0
        for i in FirstNgrams:
            NGram2ID[i] = ngramid
            ID2NGram[ngramid] = i
            ngramid+=1
        # *03* [ / making dictionaries  for  NGram_Text <=> NGram_ID ]

        docs_X_terms = {}
        for i in FreqList: # foreach ID in Doc:
            docID = i[0]
            associations = i[1]

            # [ considering just {2,3}-grams ]
            termsCount = 0
            for ngram_text, weight in associations.items():
                if ngram_text in NGram2ID: # considering just {2,3}-grams
                    termsCount+=1
            # [ / considering just {2,3}-grams ]

            ngrams_by_document = termsCount # i re-calculed this because of *02*
            terms = []
            terms_occ = []
            if ngrams_by_document > 0:
                for ngram_text, weight in associations.items():
                    if ngram_text in NGram2ID:
                        terms.append(NGram2ID[ngram_text])
                        # [ calculating TF-IDF ]
                        occurrences_of_ngram = weight
                        term_frequency = occurrences_of_ngram / ngrams_by_document
                        xx = N
                        yy = FirstNgrams[ngram_text]["C"]
                        inverse_document_frequency= log(xx/yy) #log base e
                        tfidfScore = term_frequency*inverse_document_frequency

                        terms_occ.append( [ NGram2ID[ngram_text] ,  round(tfidfScore,3) ]  )

                        # [ / calculating TF-IDF ]
                        if "T" in FirstNgrams[ngram_text]:
                            FirstNgrams[ngram_text]["T"].append(tfidfScore)
                        else: 
                            FirstNgrams[ngram_text]["T"] = [tfidfScore]

                if len(terms)>1:
                    docs_X_terms[docID] = terms_occ
                    # print("docid:",docID)
                    # for i in terms:
                    #     print("\t",ID2NGram[i])
                    calc.addCompleteSubGraph(terms)

        return { "G":calc.G , "TERMS": ID2NGram , "ii":docs_X_terms ,"metrics":FirstNgrams }

    def do_coocmatrix__MOV(self , TERMS , G , n=150 , type='node_link'):
        import pandas as pd
        from copy import copy
        import numpy as np
        import networkx as nx
        from networkx.readwrite import json_graph
        from gargantext_web.api import JsonHttpResponse
        from analysis.louvain import best_partition

        matrix = defaultdict(lambda : defaultdict(float))
        ids    = dict()
        labels = dict()
        weight = dict()

        print("PRINTING NUMBER OF NODES 01:",len(G))
        for e in G.edges_iter():
            n1 = e[0]
            n2 = e[1]
            w = G[n1][n2]['weight']
            # print(n1," <=> ",n2, " : ", G[n1][n2]['weight'],"\t",TERMS[n1]," <=> ",TERMS[n2], "\t", G[n1][n2]['weight'])
            ids[TERMS[n1]] = n1
            ids[TERMS[n2]] = n2

            labels[n1] = TERMS[n1]
            labels[n2] = TERMS[n2]

            matrix[ n1 ][ n2 ] = w
            matrix[ n2 ][ n1 ] = w

            weight[n2] = weight.get( n2, 0) + w
            weight[n1] = weight.get( n1, 0) + w

        df = pd.DataFrame(matrix).fillna(0)
        x = copy(df.values)
        x = x / x.sum(axis=1)

        # Removing unconnected nodes
        threshold = min(x.max(axis=1))
        matrix_filtered = np.where(x >= threshold, 1, 0)
        #matrix_filtered = np.where(x > threshold, x, 0)
        #matrix_filtered = matrix_filtered.resize((90,90))
        G = nx.from_numpy_matrix(matrix_filtered)
        # G = nx.relabel_nodes(G, dict(enumerate([ labels[label] for label in list(df.columns)])))

        partition = best_partition(G)

        data = []
        if type == "node_link":
            for community in set(partition.values()):
                G.add_node("cluster " + str(community), hidden=1)
            for node in G.nodes():
                try:
                    G.node[node]['label']   = TERMS[node]
                    G.node[node]['pk']      = node
                    G.node[node]['size']    = weight[node]
                    G.node[node]['group']   = partition[node]
                    G.add_edge(node, "cluster " + str(partition[node]), weight=3)
                except Exception as error:
                    print("ERROR:",error)
            print("PRINTING NUMBER OF NODES 02:",len(G))
            data = json_graph.node_link_data(G)

        elif type == "adjacency":
            for node in G.nodes():
                try:
                    #node,type(labels[node])
                    #G.node[node]['label']   = node
                    G.node[node]['name']    = node
                    #G.node[node]['size']    = weight[node]
                    G.node[node]['group']   = partition[node]
                    #G.add_edge(node, partition[node], weight=3)
                except Exception as error:
                    print(error)
            data = json_graph.node_link_data(G)
        
        return data

    def workflow__MOV(self, keys=None, ngramsextractorscache=None, ngramscaches=None, verbose=False):
        import time
        total = 0
        self.metadata['Processing'] = 1
        self.save()

        # # pwd = subprocess.Popen("cd /srv/gargantext/parsing/Taggers/nlpserver && pwd", stdout=subprocess.PIPE).stdout.read()
        # # print(subprocess.Popen(['ls', '-lah'], stdout=subprocess.PIPE).communicate()[0].decode('utf-8'))
        # print("activating nlpserver:")
        # command = 'cd parsing/Taggers/nlpserver; python3 server.py'
        # process = subprocess.Popen(command,stdout=subprocess.PIPE , stderr=subprocess.DEVNULL , shell=True)
        


        print("LOG::TIME: In workflow()    parse_resources__MOV()")
        start = time.time()
        theMetadata = self.parse_resources__MOV()
        end = time.time()
        total += (end - start)
        print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" parse_resources()__MOV [s]",(end - start))

        
        print("LOG::TIME: In workflow()    writeMetadata__MOV()")
        start = time.time()
        theMetadata = self.writeMetadata__MOV( metadata_list=theMetadata )
        end = time.time()
        total += (end - start)
        print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" writeMetadata__MOV() [s]",(end - start))

        print("LOG::TIME: In workflow()    extract_ngrams__MOV()")
        start = time.time()
        FreqList = self.extract_ngrams__MOV(theMetadata , keys=['title'] )
        end = time.time()
        total += (end - start)
        print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" extract_ngrams__MOV() [s]",(end - start))

        # process.kill()
        # print("ok, process killed")

        start = time.time()
        print("LOG::TIME: In workflow()    do_tfidf()")
        resultDict = self.do_tfidf__MOV( FreqList , theMetadata)
        end = time.time()
        total += (end - start)
        print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" do_tfidf() [s]",(end - start))
        # # print("LOG::TIME: In workflow()    / do_tfidf()")

        start = time.time()
        print("LOG::TIME: In workflow()    do_coocmatrix()")
        jsongraph = self.do_coocmatrix__MOV ( resultDict["TERMS"] , resultDict["G"] , n=150)
        jsongraph["stats"] = resultDict["ii"]
        end = time.time()
        total += (end - start)
        print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" do_coocmatrix() [s]",(end - start))

        print("the user:",self.user)
        print("the project id:",self.parent.id)
        print("the corpus id:",self.id)
        # timestamp = str(datetime.datetime.now().isoformat())
        # # filename = MEDIA_ROOT + '/corpora/%s/%s_%s__%s.json' % (self.user , self.parent.id, self.id , timestamp)
        filename = MEDIA_ROOT + '/corpora/%s/%s_%s.json' % (self.user , self.parent.id, self.id)
        import json
        f = open(filename,"w")
        f.write( json.dumps(jsongraph) )
        f.close()


        # # # this is not working
        # # self.runInParallel( self.writeMetadata__MOV( metadata_list=theMetadata ) , self.extract_ngrams__MOV(theMetadata , keys=['title','abstract',] ) )
        
        print("LOG::TIME:_ "+datetime.datetime.now().isoformat()+"   In workflow() END")


        self.metadata['Processing'] = 0
        self.save()

class Node_Metadata(models.Model):
    node        = models.ForeignKey(Node, on_delete=models.CASCADE)
    metadata    = models.ForeignKey(Metadata)
    value_int   = models.IntegerField(null=True, db_index=True)
    value_float = models.FloatField(null=True, db_index=True)
    value_string = models.CharField(max_length=255, null=True, db_index=True)
    value_datetime  = models.DateTimeField(null=True, db_index=True)
    value_text  = models.TextField(null=True)

class Node_Resource(models.Model):
    node     = models.ForeignKey(Node, related_name='node_resource', on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource)
    parsed   = models.BooleanField(default=False)
            
class Node_Ngram(models.Model):
    node   = models.ForeignKey(Node, on_delete=models.CASCADE)
    ngram  = models.ForeignKey(Ngram)
    weight = models.FloatField()
    def __str__(self):
        return "%s: %s" % (self.node.name, self.ngram.terms)

class Project(Node):
    class Meta:
        proxy=True

class Corpus(Node):
    class Meta:
        proxy=True
        verbose_name_plural = 'Corpora'

#class WhiteList(Node):
#    class Meta:
#        proxy=True
#
#class BlackList(Node):
#    class Meta:
#        proxy=True
#
#class Synonyms(Node):
#    class Meta:
#        proxy=True

class Document(Node):
    class Meta:
        proxy=True

class NodeNgramNgram(models.Model):
    node        = models.ForeignKey(Node, on_delete=models.CASCADE)
    
    ngramx      = models.ForeignKey(Ngram, related_name="nodengramngramx", on_delete=models.CASCADE)
    ngramy      = models.ForeignKey(Ngram, related_name="nodengramngramy", on_delete=models.CASCADE)

    score       = models.FloatField(default=0)

    def __str__(self):
        return "%s: %s / %s" % (self.node.name, self.ngramx.terms, self.ngramy.terms)


class NodeNodeNgram(models.Model):
    nodex        = models.ForeignKey(Node, related_name="nodex", on_delete=models.CASCADE)
    nodey        = models.ForeignKey(Node, related_name="nodey", on_delete=models.CASCADE)
    
    ngram      = models.ForeignKey(Ngram, on_delete=models.CASCADE)

    score       = models.FloatField(default=0)

    def __str__(self):
        return "%s: %s / %s = %s" % (self.nodex.name, self.nodey.name, self.ngram.terms, self.score)

class NodeNodeNgram(models.Model):
    nodex        = models.ForeignKey(Node, related_name="nodex", on_delete=models.CASCADE)
    nodey        = models.ForeignKey(Node, related_name="nodey", on_delete=models.CASCADE)
    
    ngram      = models.ForeignKey(Ngram, on_delete=models.CASCADE)

    score       = models.FloatField(default=0)

    def __str__(self):
        return "%s: %s / %s = %s" % (self.nodex.name, self.nodey.name, self.ngram.terms, self.score)


