from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


from node.models import Node, Language

class Ngram(models.Model):
    language    = models.ForeignKey(Language, blank=True, null=True, on_delete=models.SET_NULL)
    n           = models.IntegerField()
    terms       = models.CharField(max_length=255)
    def __str__(self):
        return "[%d] %s" % (self.pk, self.terms)

class NodeNgram(models.Model):
    node        = models.ForeignKey(Node)
    ngram       = models.ForeignKey(Ngram, related_name="nodengram")
    def __str__(self):
        return "%s: %s" % (self.node.name, self.ngram.terms)

class NodeNgramNgram(models.Model):
    node        = models.ForeignKey(Node)
    
    ngramX      = models.ForeignKey(Ngram, related_name="nodengramngramx")
    ngramY      = models.ForeignKey(Ngram, related_name="nodengramngramy")

    score       = models.FloatField(default=0)

    def __str__(self):
        return "%s: %s / %s" % (self.node.name, self.ngramX.terms, self.ngramY.terms)


