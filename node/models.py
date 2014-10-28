from django.db import models
from django.utils import timezone

from django_hstore import hstore
from cte_tree.models import CTENode, Manager
#from cte_tree.fields import DepthField, PathField, OrderingField

from time import time

from django.contrib.auth.models import User

from collections import defaultdict

# Some usefull functions

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

#class Ngram(models.Model):
#    language    = models.ForeignKey(Language, blank=True, null=True, on_delete=models.SET_NULL)
#    n           = models.IntegerField()
#    terms       = models.CharField(max_length=255)

class Resource(models.Model):
    user        = models.ForeignKey(User)
    guid        = models.CharField(max_length=255)
    bdd_type    = models.ForeignKey(DatabaseType, blank=True, null=True)
    file        = models.FileField(upload_to=upload_to, blank=True)
    def __str__(self):
        return "%s => %s" % (self.bdd_type, self.file)

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
    
    resource    = models.ManyToManyField(Resource, blank=True)
    ngrams      = models.ManyToManyField(Ngram, blank=True, help_text="Hold down")
    
    
    def __str__(self):
        return self.name

    def liste(self, user):
        for noeud in Node.objects.filter(user=user):
            print(noeud.depth * "    " + "[%d] %d" % (noeud.pk, noeud.name))

class Node_Ngram(models.Model):
    node        = models.ForeignKey(Node, on_delete=models.CASCADE)
    ngram       = models.ForeignKey(Ngram, on_delete=models.CASCADE)
    occurences  = models.IntegerField()

class Project(Node):
    class Meta:
        proxy=True

class CorpusManager(models.Manager):
    def get_query_set(self):
        corpus_type = NodeType.objects.get(name='Corpus')
        return super(CorpusManager, self).get_query_set().filter(type=corpus_type)

class Corpus(Node):
    objects = CorpusManager()
    
    class Meta:
        proxy=True
        verbose_name_plural = 'Corpora'

class Document(Node):
    class Meta:
        proxy=True


