

from django.contrib.auth.models import User
from documents.models import Project, Corpus, Document, Source, Language
from sources import importateur
from analysis import extract

try:
    user = User.objects.get(username="alexandre")
except Exception as e:
    print(e, "Error user")


# LANGUAGES
try:
    french = Language.objects.get(language = "Français")
except:
    french = Language()
    french.language = "Français"
    french.save()

try:
    english = Language.objects.get(language = "English")
except:
    english = Language()
    english.language = "English"
    english.save()


### DATABASES
try:
    presse = Source.objects.get(database="Europresse")
except:
    presse = Source()
    presse.database = "Europresse"
    presse.save()


try:
    science = Source.objects.get(database="Web of Science (ISI format)")
except:
    science = Source()
    science.database = "Web of Science (ISI format)"
    science.save()


# PROJECT
try:
    p = Project.objects.get(title = "[TEST] Les abeilles")
except:
    p = Project()
    p.title = "[TEST] Les abeilles"
    p.user  = user
    p.save()

# CORPORA

try:
    c = Corpus.objects.get(title = "Presse francophone")
except:
    c = Corpus()
    c.project = p
    c.database = presse
    c.language = french
    
    c.title = "Presse francophone"
    c.user  = user
    c.zip_file = "corpora/" + user.username + "/" + "html_french.zip"
    c.save()


try:
    i = Corpus.objects.get(title = "Science ISI WOS")
    i.zip_file = "corpora/" + user.username + "/" + "pesticidesOnly.zip"
    i.save()
except:
    i = Corpus()
    i.project = p
    i.database = science
    i.language = french
    
    i.title = "Science ISI WOS"
    i.user  = user
    i.zip_file = "corpora/" + user.username + "/" + "isi.zip"
    i.save()


def test_import(corpus):
    try:
# TODO factorization here
        importateur.importer(corpus.database, corpus.language, corpus.zip_file, project=corpus.project, corpus=corpus, user=corpus.user)
    except Exception as e:
        print(e)

#test_import(i)

def test_words(corpus, field='abstract'):
    try:
        extract.words_field(corpus, field=field)
    except Exception as e: print(e)

test_words(i)

