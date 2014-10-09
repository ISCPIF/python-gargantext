from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

from django_hstore import hstore
from treebeard.mp_tree import MP_Node

from time import time

def upload_to(instance, filename):
    return 'corpora/%s/%f/%s' % (instance.user.username, time(), filename)


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


