from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

from django_hstore import hstore

from treebeard.mp_tree import MP_Node
from cte_tree.models import CTENode

from time import time

def upload_to(instance, filename):
    return 'corpora/%s/%f/%s' % (instance.user.username, time(), filename)

    
class Resource(models.Model):
    guid        = models.CharField(max_length=255)
    file        = models.FileField(upload_to=upload_to, blank=True)

class NodeType(models.Model):
    name        = models.CharField(max_length=200)
    def __str__(self):
        return self.name

class Node(MP_Node):
    #parent = models.ForeignKey('self', related_name='children_set', null=True, db_index=True)
    user        = models.ForeignKey(User)
    type        = models.ForeignKey(NodeType)
    name        = models.CharField(max_length=200)
    
    date        = models.DateField(default=timezone.now(), blank=True)
    metadata    = hstore.DictionaryField(blank=True)
    
    # the 'file' column should be deprecated soon;
    # use resources instead.
    file        = models.FileField(upload_to=upload_to, blank=True)
    #resources   = models.ManyToManyField(Resource)
    
    #objects    = hstore.HStoreManager()
    def __str__(self):
        return self.name

    def liste(self, user):
        for noeud in Node.objects.filter(user=user):
            print(noeud.depth * "    " + "[%d] %d" % (noeud.pk, noeud.name))

class Nodec(CTENode):
    user        = models.ForeignKey(User)
    type        = models.ForeignKey(NodeType)
    name        = models.CharField(max_length=200)
    
    date        = models.DateField(default=timezone.now(), blank=True)
    metadata    = hstore.DictionaryField(blank=True)
    
    # the 'file' column should be deprecated soon;
    # use resources instead.
    file        = models.FileField(upload_to=upload_to, blank=True)
    #resources   = models.ManyToManyField(Resource)
    
    #objects    = hstore.HStoreManager()
    def __str__(self):
        return self.name

    def liste(self, user):
        for noeud in Node.objects.filter(user=user):
            print(noeud.depth * "    " + "[%d] %d" % (noeud.pk, noeud.name))


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


