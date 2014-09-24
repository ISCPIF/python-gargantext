
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django_hstore import hstore


######################################################################
# DATABASES / LANGUAGES 
# PROJECT / CORPUS / DOCUMENT
######################################################################


class Source(models.Model):
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
    database    = models.ForeignKey(Source)
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
    corpus      = models.ManyToManyField(Corpus)
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
    terms    = models.CharField(max_length=64, unique=True)
    stem     = models.CharField(max_length=64, blank=True)
    n        = models.IntegerField()
# post-tag = models.ManyToMany(blank=True)
# ajouter une table stem ?
    def __str__(self):
        return self.terms

class NgramTemporary(models.Model):
    terms    = models.TextField()
    stem     = models.TextField(blank=True)
    n        = models.IntegerField()
    def __str__(self):
        return self.terms

class NgramDocument(models.Model):
    terms       = models.ForeignKey(Ngram)
    document    = models.ForeignKey(Document)
    occurrences = models.IntegerField(default=1, blank=True, null=True)
    def __str__(self):
        return self.terms.terms

class NgramDocumentTemporary(models.Model):
    terms       = models.TextField(blank=True)
    document    = models.IntegerField(blank=True)
    occurrences = models.IntegerField(blank=True, null=True)
    def __str__(self):
        return self.terms

class List(models.Model):
    title       = models.CharField(max_length=100, unique=True)
    analyst     = models.ForeignKey(User)
    date        = models.DateField(default=timezone.now(), verbose_name="Date of creation")
    TYPES       = ((1,"Black List"), (2,"White List"), (3,"Grey List"))
    type_list   = models.IntegerField(choices=TYPES)
    corpus      = models.ManyToManyField(Corpus, related_name="relatedCorpus", blank=True)
    def __str__(self):
        return self.title

class ListNgram(models.Model):
    liste       = models.ForeignKey(List)
    mainForm    = models.ForeignKey(Ngram, related_name="mainForm")
    othersForms = models.ManyToManyField(Ngram, related_name="otherForms", blank=True)
    cvalue      = models.DecimalField(max_digits=19, decimal_places=10, blank=True, null=True)
    def __str__(self):
        return self.mainForm.terms

#class Postag(models.Model):
#    abrev       = models.CharField(max_length=30, unique=True)
#    description = models.TextField(blank=True)
#    def __str__(self):
#        return(self.abrev)

######################################################################
# Coocurrences
# Graph
######################################################################

class Coocurrence(models.Model):
    title       = models.CharField(max_length=100)
    corpus      = models.ForeignKey(Corpus)
    whitelists  = models.ManyToManyField(List)

    ngram1      = models.ForeignKey(Ngram, related_name="x")
    ngram2      = models.ForeignKey(Ngram, related_name="y")

    occurrence  = models.IntegerField()
    distance    = models.DecimalField(max_digits=19, decimal_places=10,blank=True)
    def __str__(self):
        return self.title


# graph ?


