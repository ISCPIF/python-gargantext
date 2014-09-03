from django.db import models

# Create your models here.

from django.utils import timezone
from django_hstore import hstore


class CorpusType(models.Model):
    """
    Web Of Science, Europresse, Pubmed...
    """
    def __str__(self):
        return self.corpus_type
    corpus_type      = models.CharField(max_length=25, unique=True)


class Language(models.Model):
    """
    French or english or...
    """
    def __str__(self):
        return self.language
    language        = models.CharField(max_length=15, unique=True)


class Corpus(models.Model):
    def __str__(self):
        return self.title
    corpus_type = models.ForeignKey(CorpusType)
    language    = models.ForeignKey(Language, blank=True, null=True)
    date        = models.DateField(default=timezone.now(), verbose_name="Date End")

    title       = models.CharField(max_length=300, blank=True)
    subtitle    = models.CharField(max_length=300, blank=True)
    
    zip_file    = models.FileField(upload_to='documents', blank=True)

    others      = hstore.DictionaryField(blank=True)
    objects     = hstore.HStoreManager()


class Document(models.Model):
    def __str__(self):
        return self.title
    date        = models.DateField(blank=True, null=True)
    # corpus_source foreign vers corpus
# unique_id

    authors     = models.ManyToManyField(Author, through='Authored', blank=True)
    institution = models.ManyToManyField(Institution, blank=True, null=True)
    
    name            = models.CharField(help_text="Journal/Seminar/Book Name", max_length=300, blank=True)
    issue_title     = models.CharField(help_text="Special issue title if any", max_length=250, blank=True)
    chapter         = models.CharField(max_length=300, blank=True)
    title           = models.CharField(max_length=300, blank=True)
    subtitle        = models.CharField(max_length=300, blank=True)
    source          = models.CharField(max_length=100, blank=True)
    
    keywords    = models.CharField(max_length=300, blank=True)
    bibtex_id   = models.CharField(max_length=50, blank=True)
    
    volume      = models.IntegerField(blank=True, null=True)
    number      = models.IntegerField(blank=True, null=True)
    start_page  = models.IntegerField(blank=True, null=True)
    end_page    = models.IntegerField(blank=True, null=True)
    
    editors     = models.CharField(verbose_name="Editors Names", max_length=200, blank=True)
    publisher   = models.CharField(max_length=300, blank=True)
    country     = models.ForeignKey(Country, blank=True, null=True)
    address     = models.CharField(max_length=200, blank=True)
    url         = models.URLField(blank=True)
    
    abstract    = models.TextField(blank=True)
    text        = models.TextField(blank=True)
    paper       = models.FileField(upload_to='documents', blank=True)

    others      = hstore.DictionaryField(blank=True)
    objects     = hstore.HStoreManager()


# class relation corpus / document (pour enlever des documents d'un corpus)

# table ngrams
# table relation ngrams / document
# table relation ngrams / ngrams


# table cooccrrences
# table 


