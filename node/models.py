from django.db import models
from django.utils import timezone

from django_hstore import hstore
from cte_tree.models import CTENode, Manager
#from cte_tree.fields import DepthField, PathField, OrderingField

from time import time

from django.contrib.auth.models import User

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

class DatabaseType(models.Model):
    name    = models.CharField(max_length=255)
    def __str__(self):
        return self.name

class Ngram(models.Model):
    language    = models.ForeignKey(Language, blank=True, null=True, on_delete=models.SET_NULL)
    n           = models.IntegerField()
    terms       = models.CharField(max_length=255)

class Resource(models.Model):
    guid        = models.CharField(max_length=255)
    bdd_type    = models.ForeignKey(DatabaseType, blank=True, null=True)
    file        = models.FileField(upload_to=upload_to, blank=True)
    digest      = models.CharField(max_length=32) # MD5 digest

class NodeType(models.Model):
    name        = models.CharField(max_length=200)
    def __str__(self):
        return self.name

class Node(CTENode):
    objects     = Manager()

    user        = models.ForeignKey(User)
    type        = models.ForeignKey(NodeType)
    name        = models.CharField(max_length=200)
    
    language    = models.ForeignKey(Language, blank=True, null=True, on_delete=models.SET_NULL)
    
    date        = models.DateField(default=timezone.now, blank=True)
    metadata    = hstore.DictionaryField(blank=True)

    # TODO: remove the three following fields
    fichier      = models.FileField(upload_to=upload_to, blank=True)
    #resource    = models.ForeignKey(Resource, blank=True, null=True)
    #ngrams      = models.ManyToManyField(NGrams)
    
    
    def __str__(self):
        return self.name
    
    # TODO: voir à quoi sert cette méthode
    def liste(self, user):
        for noeud in Node.objects.filter(user=user):
            print(noeud.depth * "    " + "[%d] %d" % (noeud.pk, noeud.name))
    
    
    
    
    def add_resource(self, **kwargs):
        resource = Resource(**kwargs)
        # TODO: vérifier si tous ces 'save' sont réellement utiles
        resource.save()
        node_resource = Node_Resource(
            node     = self,
            resource = resource
        )
        node_resource.save()
        return resource
    
    def parse(self):
        # TODO: that's not very pretty...
        # can't we make a simple join in Django?
        for node_resource in self.node_resource.filter(parsed=False):
            # TODO: call parsers here
            print(node_resource.resource.file)
    
    def extract_ngrams(self, keys, cache):
        # what do we want from the cache?
        extractor = cache.extractors[self.language]
        ngrams = cache.ngrams[self.language]
        # find & count all the occurrences
        associations = defaultdict(float) # float or int?
        if isinstance(keys, dict):
            for key, weight in keys.items():
                for ngram in extractor.extract_ngrams(self.metadata[key]):
                    associations[key] += weight
        else:
            for key in keys:
                for ngram in extractor.extract_ngrams(self.metadata[key]):
                    associations[key] += 1
        # insert the occurrences in the database
        for ngram_text, weight in associations.items():
            Node_Ngram(
                node   = self,
                ngram  = ngrams[ngram_text],
                weight = weight
            )

class Node_Resource(models.Model):
    node     = models.ForeignKey(Node, related_name='node_resource')
    resource = models.ForeignKey(Resource)
    parsed   = models.BooleanField(default=False)
            
class Node_Ngram(models.Model):
    node   = models.ForeignKey(Node)
    ngram  = models.ForeignKey(Ngram)
    weight = models.IntegerField()

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


