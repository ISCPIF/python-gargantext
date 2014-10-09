from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Ngram(models.Model):
    terms    = models.TextField(unique=True)
    n        = models.IntegerField()
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


