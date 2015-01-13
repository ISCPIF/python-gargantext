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
from collections import defaultdict
import hashlib

from gargantext_web.settings import MEDIA_ROOT

from celery.contrib.methods import task_method
from celery import current_app


# Some usefull functions
# TODO: start the function name with an underscore (private)
def _upload_to(instance, filename):
    return MEDIA_ROOT + '/corpora/%s/%s' % (instance.user.username, filename)

# All classes here

class Language(models.Model):
    iso2        = models.CharField(max_length=2, unique=True)
    iso3        = models.CharField(max_length=3)
    fullname    = models.CharField(max_length=255)
    implemented = models.BooleanField(blank=True)
    
    def __str__(self):
        return self.fullname

class ResourceType(models.Model):
    name    = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name

class Ngram(models.Model):
    language    = models.ForeignKey(Language, blank=True, null=True, on_delete=models.SET_NULL)
    n           = models.IntegerField()
    terms       = models.CharField(max_length=255)
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
    name        = models.CharField(max_length=200)
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
            print(node.id)
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




        print("printing arguments for add_resource():")
        print(kwargs)


        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        import os
        thefile = kwargs["file"]
        path = default_storage.save('tmp/somename.zip', ContentFile(thefile.read()))
        tmp_file  = os.path.join(MEDIA_ROOT, path)
        print(tmp_file)
        kwargs["file"] = tmp_file
        print("final kwargs:")
        print(kwargs)


        # only for tests
        resource = Resource(guid=str(time()), digest=str(time()), **kwargs )


        #resource = Resource(**kwargs)
        resource.save()
        print("printing rresource.file:")
        print(resource.file)
        # print("printing the resource 01____:")
        # print(resource.file)
        # print("printing the resource 02____: asdasdasd")

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
        for node_resource in self.node_resource.filter(parsed=False):
            resource = node_resource.resource
            parser = defaultdict(lambda:FileParser.FileParser, {
                'pubmed'    : PubmedFileParser,
                'isi'       : IsiFileParser,
                'ris'       : RisFileParser,
                'europress' : EuropressFileParser,
                'europress_french'  : EuropressFileParser,
                'europress_english' : EuropressFileParser,
            })[resource.type.name]()
            print("parse_resources:")
            print(resource.file)
            metadata_list += parser.parse(str(resource.file))
        # retrieve info from the database
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
                for ngram in extractor.extract_ngrams(self.metadata[key]):
                    terms = ' '.join([token for token, tag in ngram])
                    associations[ngram] += weight
        else:
            for key in keys:
                for ngram in extractor.extract_ngrams(self.metadata[key]):
                    terms = ' '.join([token for token, tag in ngram])
                    associations[terms] += 1
        #print(associations)
        # insert the occurrences in the database
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
        print("In workflow() START")
        self.parse_resources()
        type_document   = NodeType.objects.get(name='Document')
        self.children.filter(type_id=type_document.pk).extract_ngrams(keys=['title',])
        from analysis.functions import do_tfidf
        do_tfidf(self)
        print("In workflow() END")

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


