from django_pg import models
from django.utils import timezone

from django.contrib.auth.models import User

from django_pgjson.fields import JsonBField

from cte_tree.models import CTENode, CTENodeManager
# from cte_tree.query import CTEQuerySet
#from cte_tree.fields import DepthField, PathField, OrderingField

from parsing.Caches import LanguagesCache, NgramsExtractorsCache, NgramsCaches
from parsing.FileParsers import *

from time import time
import datetime
from multiprocessing import Process
from math import log

import collections
from collections import defaultdict
import hashlib

from gargantext_web.settings import MEDIA_ROOT

from celery.contrib.methods import task_method
from celery import current_app

import os
import subprocess

from parsing.parsers_config import parsers

# Some usefull functions
# TODO: start the function name with an underscore (private)
def _upload_to(instance, filename):
    return MEDIA_ROOT + '/corpora/%s/%s' % (instance.user.username, filename)

# All classes here

class Language(models.Model):
    iso2        = models.CharField(max_length=2, unique=True)
    iso3        = models.CharField(max_length=3, unique=True)
    fullname    = models.CharField(max_length=255, unique=True)
    implemented = models.BooleanField(blank=True, default=True)

    def __str__(self):
        return self.fullname

class ResourceType(models.Model):
    name    = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Tag(models.Model):
    name             = models.CharField(max_length=4, unique=True)
    description      = models.CharField(max_length=255, unique=True)
    def __str__(self):
        return self.name

class Ngram(models.Model):
    language    = models.ManyToManyField(blank=True, null=True, through='NgramLanguage', to='Language')
    n           = models.IntegerField()
    terms       = models.CharField(max_length=255, unique=True)
    nodes       = models.ManyToManyField(through='Node_Ngram', to='Node')
    tag         = models.ManyToManyField(blank=True, null=True, through='NgramTag', to='Tag')

    def __str__(self):
        return self.terms

class NgramTag(models.Model):
    ngram   = models.ForeignKey(Ngram, on_delete=models.CASCADE)
    tag     = models.ForeignKey(Tag)
    def __str__(self):
        return "%s: %s" % (self.ngram.terms, self.tag.name)

class NgramLanguage(models.Model):
    ngram        = models.ForeignKey(Ngram, on_delete=models.CASCADE)
    language     = models.ForeignKey(Language)
    def __str__(self):
        return "%s: %s" % (self.ngram.terms, self.language.fullname)

class Resource(models.Model):
    user        = models.ForeignKey(User)
    guid        = models.CharField(max_length=255)
    type        = models.ForeignKey(ResourceType, blank=True, null=True)
    file        = models.FileField(upload_to=_upload_to, blank=True)
    digest      = models.CharField(max_length=32) # MD5 digest
    def __str__(self):
        return self.file

class NodeType(models.Model):
    name        = models.CharField(max_length=255, unique=True)
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

    def make_hyperdata_filterable(self):
        hyperdata_cache = {hyperdata.name: hyperdata for hyperdata in Hyperdata.objects.all()}
        data = []
        for node in self:
            for key, value in node.hyperdata.items():
                if key in hyperdata_cache:
                    hyperdata = hyperdata_cache[key]
                    if hyperdata.type == 'string':
                        value = value[:200]
                    data.append(Node_Hyperdata(**{
                        'node_id' : node.id,
                        'hyperdata_id' : hyperdata.id,
                        ('value_'+hyperdata.type) : value,
                    }))
        Node_Hyperdata.objects.bulk_create(data)

class NodeManager(CTENodeManager):
    """Methods available from Node.object."""
    def get_queryset(self):
        self._ensure_parameters()
        return NodeQuerySet(self.model, using=self._db)
    def __getattr__(self, name, *args):
        if name.startswith("_"):
            raise AttributeError
        return getattr(self.get_queryset(), name, *args)

class Hyperdata(models.Model):
    name        = models.CharField(max_length=32, unique=True)
    type        = models.CharField(max_length=16, db_index=True)

class Node(CTENode):
    """The node."""
    objects     = NodeManager()

    user        = models.ForeignKey(User)
    type        = models.ForeignKey(NodeType)
    name        = models.CharField(max_length=255)

    language    = models.ForeignKey(Language, blank=True, null=True, on_delete=models.SET_NULL)

    date        = models.DateField(default=timezone.now, blank=True)
    hyperdata    = JsonBField(null=False, default={})

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
        # parse all resources into a list of hyperdata
        hyperdata_list = []
        print("not parsed resources:")
        print(self.node_resource.filter(parsed=False))
        print("= = = = = = = = =  = =\n")
        for node_resource in self.node_resource.filter(parsed=False):
            resource = node_resource.resource
            parser = defaultdict(lambda:FileParser.FileParser, parsers
#                    {
#                'istext'            : ISText,
#                'pubmed'            : PubmedFileParser,
#                'isi'               : IsiFileParser,
#                'ris'               : RisFileParser,
#                'RIS (Jstor)'       : JstorFileParser,
#                'europress'         : EuropressFileParser,
#                'europress_french'  : EuropressFileParser,
#                'europress_english' : EuropressFileParser,
#            }

                    )[resource.type.name]()
            hyperdata_list += parser.parse(str(resource.file))
        type_id = NodeType.objects.get(name='Document').id
        langages_cache = LanguagesCache()
        user_id = self.user.id
        # insert the new resources in the database!
        for i, hyperdata_values in enumerate(hyperdata_list):
            if verbose:
                print(i, end='\r', flush=True)
            name = hyperdata_values.get('title', '')[:200]
            language = langages_cache[hyperdata_values['language_iso2']] if 'language_iso2' in hyperdata_values else None,
            if isinstance(language, tuple):
                language = language[0]
            # print("hyperdata_values:")
            # print("\t",hyperdata_values,"\n- - - - - - - - - - - - ")
            Node(
                user_id  = user_id,
                type_id  = type_id,
                name     = name,
                parent   = self,
                language_id = language.id if language else None,
                hyperdata = hyperdata_values
            ).save()
        # make hyperdata filterable
        self.children.all().make_hyperdata_filterable()

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
                text2process = str(self.hyperdata[key]).replace('[','').replace(']','')
                for ngram in extractor.extract_ngrams(text2process):
                    terms = ' '.join([token for token, tag in ngram])
                    associations[ngram] += weight
        else:
            for key in keys:
                text2process = str(self.hyperdata[key]).replace('[','').replace(']','')
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

    # @current_app.task(filter=task_method)
    # def workflow(self, keys=None, ngramsextractorscache=None, ngramscaches=None, verbose=False):
    #     import time
    #     total = 0
    #     print("LOG::TIME: In workflow()    parse_resources()")
    #     start = time.time()
    #     self.hyperdata['Processing'] = 1
    #     self.save()
    #     self.parse_resources()
    #     end = time.time()
    #     total += (end - start)
    #     print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" parse_resources() [s]",(end - start))
    #     print("LOG::TIME: In workflow()    / parse_resources()")

    #     start = time.time()
    #     print("LOG::TIME: In workflow()    extract_ngrams()")
    #     print("\n- - - - - - - - - -")
    #     type_document   = NodeType.objects.get(name='Document')
    #     self.children.filter(type_id=type_document.pk).extract_ngrams(keys=['title',])
    #     end = time.time()
    #     print("- - - - - - - - - - \n")
    #     total += (end - start)
    #     print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" extract_ngrams() [s]",(end - start))
    #     print("LOG::TIME: In workflow()    / extract_ngrams()")

    #     start = time.time()
    #     print("In workflow()    do_tfidf()")
    #     from analysis.functions import do_tfidf
    #     do_tfidf(self)
    #     end = time.time()
    #     total += (end - start)
    #     print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" do_tfidf() [s]",(end - start))
    #     print("LOG::TIME: In workflow()    / do_tfidf()")
    #     print("In workflow() END")
    #     self.hyperdata['Processing'] = 0
    #     self.save()

class Node_Hyperdata(models.Model):
    node        = models.ForeignKey(Node, on_delete=models.CASCADE)
    hyperdata    = models.ForeignKey(Hyperdata)
    value_int   = models.IntegerField(null=True, db_index=True)
    value_float = models.FloatField(null=True, db_index=True)
    value_string = models.CharField(max_length=255, null=True, db_index=True)
    value_datetime  = models.DateTimeField(null=True, db_index=True)
    value_text  = models.TextField(null=True)

class Node_Resource(models.Model):
    node     = models.ForeignKey(Node, related_name='node_resource', on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
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

class NodeHyperdataNgram(models.Model):
    node       = models.ForeignKey(Node, on_delete=models.CASCADE)

    hyperdata      = models.ForeignKey(Hyperdata, on_delete=models.CASCADE)
    ngram          = models.ForeignKey(Ngram, on_delete=models.CASCADE)

    score       = models.FloatField(default=0)

    def __str__(self):
        return "%s: %s / %s" % (self.node.name, self.hyperdata.value_string, self.ngram.terms)


class NodeNodeNgram(models.Model):
    nodex        = models.ForeignKey(Node, related_name="nodex", on_delete=models.CASCADE)
    nodey        = models.ForeignKey(Node, related_name="nodey", on_delete=models.CASCADE)

    ngram      = models.ForeignKey(Ngram, on_delete=models.CASCADE)

    score       = models.FloatField(default=0)

    def __str__(self):
        return "%s: %s / %s = %s" % (self.nodex.name, self.nodey.name, self.ngram.terms, self.score)


class NgramNgram(models.Model):
    ngram      = models.ForeignKey(Ngram, related_name='ngram', on_delete=models.CASCADE)
    token      = models.ForeignKey(Ngram, related_name='token', on_delete=models.CASCADE)
    index      = models.IntegerField()


# Core Collaboration Structure

class Group(models.Model):
    '''
    The creator of the group is a user who
        - is in it
        - has all acccess by defautl
    '''
    creator       = models.ForeignKey(User)
    name          = models.CharField(max_length=255, unique=True)
    parameters    = JsonBField(null=False, default={})

    def __str__(self):
        return self.creator, self.name

class UserGroup(models.Model):
    '''
    User can have rights to the group:
        - access (read)
        - add/remove users from it (write)
    '''
    user     = models.ForeignKey(User)
    group    = models.ForeignKey(Group)
    rights   = models.CharField(max_length=1, unique=True)

    def __str__(self):
        return self.user, self.group

class NodeGroup(models.Model):
    '''
    User can have rights on the node:
        - can read (read as "r" rights)
        - can modify, remove (write as "w" rights)
    '''
    node     = models.ForeignKey(Node)
    group    = models.ForeignKey(Group)
    rights   = models.CharField(max_length=1, unique=True)

    def __str__(self):
        return self.node, self.group, self.rights


