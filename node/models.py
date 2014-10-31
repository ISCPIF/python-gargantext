from django.db import models
from django.utils import timezone

from django.contrib.auth.models import User

from django_hstore import hstore
from cte_tree.models import CTENode, Manager
#from cte_tree.fields import DepthField, PathField, OrderingField

from parsing.Caches import LanguagesCache, NgramsExtractorsCache, NgramsCaches
from parsing.FileParsers import *
from time import time
from collections import defaultdict



# Some usefull functions
# TODO: start the function name with an underscore (private)
def upload_to(instance, filename):
    return 'corpora/%s/%s' % (instance.user.username, filename)
    #return 'corpora/%s/%f/%s' % (instance.user.username, time(), filename)

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

class Resource(models.Model):
    guid        = models.CharField(max_length=255)
    type        = models.ForeignKey(ResourceType, blank=True, null=True)
    file        = models.FileField(upload_to=upload_to, blank=True)
    digest      = models.CharField(max_length=32) # MD5 digest

class NodeType(models.Model):
    name        = models.CharField(max_length=200)
    def __str__(self):
        return self.name

        
class NodeQuerySet(models.query.QuerySet):
    """Methods available from Node querysets."""
    def extract_ngrams(self, keys, ngramsextractorscache=None, ngramscaches=None):
        if ngramsextractorscache is None:
            ngramsextractorscache = NgramsExtractorsCache()
        if ngramscaches is None:
            ngramscaches = NgramsCaches()
        for node in self:
            node.extract_ngrams(keys, ngramsextractorscache, ngramscaches)
    
class NodeManager(models.Manager):
    """Methods available from Node.object."""
    def get_queryset(self):
        return NodeQuerySet(self.model)
    def __getattr__(self, name, *args):
        if name.startswith("_"): 
            raise AttributeError
        return getattr(self.get_queryset(), name, *args)
        
class Node(CTENode):
    """The node."""
    objects     = NodeManager()

    user        = models.ForeignKey(User)
    type        = models.ForeignKey(NodeType)
    name        = models.CharField(max_length=200)
    
    language    = models.ForeignKey(Language, blank=True, null=True, on_delete=models.SET_NULL)
    
    date        = models.DateField(default=timezone.now, blank=True)
    metadata    = hstore.DictionaryField(blank=True)

    # TODO: remove the three following fields
    #fichier      = models.FileField(upload_to=upload_to, blank=True)
    #resource    = models.ForeignKey(Resource, blank=True, null=True)
    #ngrams      = models.ManyToManyField(NGrams)
    
    
    def __str__(self):
        return self.name
    
    
    def add_resource(self, **kwargs):
        # only for tests
        resource = Resource(guid=str(time()), digest=str(time()), **kwargs )
        
        # TODO: vérifier si tous ces 'save' sont réellement utiles
        resource.save()
        node_resource = Node_Resource(
            node     = self,
            resource = resource
        )
        node_resource.save()
        return resource
    
    def parse_resources(self):
        # parse all resources into a list of metadata
        metadata_list = []
        for node_resource in self.node_resource.filter(parsed=False):
            resource = node_resource.resource
            parser = defaultdict(lambda:FileParser.FileParser, {
                'pubmed'    : PubmedFileParser,
                'isi'       : IsiFileParser,
                'ris'       : RisFileParser,
                'europress' : EuropressFileParser,
            })[resource.type.name]()
            metadata_list += parser.parse(str(resource.file))
        # insert the new resources in the database!
        type = NodeType.objects.get(name='Document')
        langages_cache = LanguagesCache()
        Node.objects.bulk_create([
            Node(
                user        = self.user,
                type        = type,
                name        = metadata['title'][0:199] if 'title' in metadata else '',
                parent      = self,
                language    = langages_cache[metadata['language_iso2']] if 'language_iso2' in metadata else None,
                metadata    = metadata,
            )
            for metadata in metadata_list
        ])
        # mark the resources as parsed for this node
        self.node_resource.update(parsed=True)
    
    def extract_ngrams(self, keys, ngramsextractorscache=None, ngramscaches=None):
        # if there is no cache...
        if ngramsextractorscache is None:
            ngramsextractorscache = NgramsExtractorsCache()
        if ngramscaches is None:
            ngramscaches = NgramsCaches()
        # what do we want from the cache?
        extractor = ngramsextractorscache[self.language]
        ngrams = ngramscaches[self.language]
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
        # insert the occurrences in the database
        Node_Ngram.objects.bulk_create([
            Node_Ngram(
                node   = self,
                ngram  = ngrams[ngram_text],
                weight = weight
            )
            for ngram_text, weight in associations.items()
        ])


class Node_Resource(models.Model):
    node     = models.ForeignKey(Node, related_name='node_resource')
    resource = models.ForeignKey(Resource)
    parsed   = models.BooleanField(default=False)
            
class Node_Ngram(models.Model):
    node   = models.ForeignKey(Node)
    ngram  = models.ForeignKey(Ngram)
    weight = models.FloatField()

class Project(Node):
    class Meta:
        proxy=True

class Corpus(Node):
    class Meta:
        proxy=True
        verbose_name_plural = 'Corpora'

class Document(Node):
    class Meta:
        proxy=True


