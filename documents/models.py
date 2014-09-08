
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django_hstore import hstore


######################################################################
# DATABASES / LANGUAGES 
# PROJECT / CORPUS / DOCUMENT
######################################################################


class Database(models.Model):
    """
    Web Of Science, Europresse, Pubmed...
    """
    def __str__(self):
        return self.database
    database      = models.CharField(max_length=50, unique=True)

class Language(models.Model):
    """
    French or english or...
    """
    def __str__(self):
        return self.language
    language        = models.CharField(max_length=30, unique=True)


class Project(models.Model):
    date        = models.DateField(default=timezone.now(), verbose_name="Date of creation")
    analyst     = models.ForeignKey(User, related_name='entries')

    title       = models.CharField(max_length=300, blank=True)
    subtitle    = models.CharField(max_length=300, blank=True)

    others      = hstore.DictionaryField(blank=True)
    objects     = hstore.HStoreManager()

    #class Meta:
        #get_latest_by = 'date'
        #ordering = ('-date',)
        #verbose_name_plural = 'entries'
    
    def __str__(self):
        return self.title


class Corpus(models.Model):
    project     = models.ForeignKey(Project)
    database    = models.ForeignKey(Database)
    language    = models.ForeignKey(Language)
    
    date        = models.DateField(default=timezone.now(), verbose_name="Date of creation")
    analyst     = models.ForeignKey(User)

    title       = models.CharField(max_length=300, blank=True)
    subtitle    = models.CharField(max_length=300, blank=True)
    
    zip_file    = models.FileField(upload_to='documents', blank=True)

    others      = hstore.DictionaryField(blank=True, null=True)
    objects     = hstore.HStoreManager()

    class Meta:
        get_latest_by = 'date'
        ordering = ('-date',)
        verbose_name_plural = 'corpora'
    
    def __str__(self):
        return self.title


class Document(models.Model):
    project     = models.ForeignKey(Project)
    corpus      = models.ForeignKey(Corpus)
    #corpus      = models.ManyToManyField(Corpus)
    analyst     = models.ForeignKey(User)
    
    date        = models.DateField(blank=True, null=True)

    uniqu_id    = models.CharField(max_length=150, unique=True)

    title       = models.CharField(max_length=300, blank=True)
    source      = models.CharField(max_length=150, blank=True)
    authors     = models.TextField(blank=True)

    country     = models.CharField(max_length=100, blank=True)
    url         = models.URLField(blank=True)
    
    abstract    = models.TextField(blank=True)
    text        = models.TextField(blank=True)

    others      = hstore.DictionaryField(blank=True)
    objects     = hstore.HStoreManager()
    
    class Meta:
        get_latest_by = 'date'
        ordering = ('-date',)
        #verbose_name_plural = 'entries'
    
    def __str__(self):
        return self.title

# class relation corpus / document (pour enlever des documents d'un corpus)

######################################################################
# NGRAM / NgramDocument
# LIST / ListNgram
######################################################################

class Ngram(models.Model):
    grams    = models.CharField(max_length=100, unique=True)
    n        = models.IntegerField()
#stem

class NgramDocument(models.Model):
    ngram       = models.ForeignKey(Ngram)
    document    = models.ForeignKey(Document)
    occurrences = models.IntegerField()

class List(models.Model):
    title       = models.CharField(max_length=100, unique=True)
    analyst     = models.ForeignKey(User)
# public analyst (as postgres)

class ListNgram(models.Model):
    title       = models.ForeignKey(List)
    mainForm    = models.ForeignKey(Ngram)
    othersForms = models.ManyToManyField(Ngram)

######################################################################
# Coocurrences
# Graph
######################################################################


class Coocurrence(models.Model):
    corpus      = models.ForeignKey(Corpus)
    
    ngram1      = models.ForeignKey(Ngram)
    ngram2      = models.ForeignKey(Ngram)
    
    occurrence  = models.IntegerField()
    distance    = models.DecimalField()


# graph ?


