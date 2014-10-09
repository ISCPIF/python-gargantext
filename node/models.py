
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

from django_hstore import hstore
from treebeard.mp_tree import MP_Node


def upload_to(instance, filename):
    return 'corpora/%s/%s' % (instance.user.username, filename)


class NodeType(models.Model):
    name       = models.CharField(max_length=200)
    def __str__(self):
        return self.name


class Node(MP_Node):
    #parent = models.ForeignKey('self', related_name='children_set', null=True, db_index=True)
    user       = models.ForeignKey(User)
    type       = models.ForeignKey(NodeType)
    name       = models.CharField(max_length=200)
    
    date       = models.DateField(default=timezone.now(), blank=True)
    file       = models.FileField(upload_to=upload_to, blank=True)
    metadata   = hstore.DictionaryField(blank=True)
    
    #objects    = hstore.HStoreManager()
    def __str__(self):
        return self.name

class Project(Node):
    class Meta:
        proxy=True

class Corpus(Node):
    class Meta:
        proxy=True

class Document(Node):
    class Meta:
        proxy=True


class Ngram(models.Model):
    terms    = models.TextField(unique=True)
    stem     = models.TextField(blank=True)
    n        = models.IntegerField()
    # post-tag = models.ManyToMany(blank=True)
    # ajouter une table stem ?
    def __str__(self):
        return self.terms


class NodeNgramNgram(models.Model):
    ngramX      = models.ForeignKey(Ngram, related_name="X")
    ngramY      = models.ForeignKey(Ngram, related_name="Y")

    node        = models.ForeignKey(Node)
    score       = models.DecimalField(max_digits=19, decimal_places=10,blank=True)

    def __str__(self):
        return self.node


