
# import Celery here

from documents.models import Document
from sources.europresse import Europresse
from sources.isi import Isi
from sources.pubmed import Pubmed

import zipfile

def importer(source, language, zip_file, project=None, corpus=None, user=None):
    
    ids = set([ doc.uniqu_id for doc in Document.objects.filter(corpus=corpus)])
    
    if source.database == "Europresse":
        try:
            print("Europresse DB detected")
            c = Europresse()
            if zipfile.is_zipfile(zip_file):
                with zipfile.ZipFile(zip_file, 'r') as z:
                    for fichiers in z.namelist():
                        fichier = z.open(fichiers, 'r')
                        c.parse(fichier)
                        c.add(project=project, corpus=corpus, user=user, ids=ids)

        except Exception as e:
            print(e)
    
    elif source.database == "Web of Science (ISI format)":
        try:
            print("ISI DB detected")
            c = Isi()
            if zipfile.is_zipfile(zip_file):
                with zipfile.ZipFile(zip_file, 'r') as z:
                    for fichiers in z.namelist():
                        print("parsing %s" % (fichiers))
                        fichier = z.open(fichiers, 'r')
                        c.parse(fichier, bdd='isi')
                        c.add(project=project, corpus=corpus, user=user, ids=ids)

        except Exception as e:
            print(e)
    
    elif source.database == "RIS (Zotero)":
        try:
            print("RIS DB detected")
            c = Isi()
            if zipfile.is_zipfile(zip_file):
                with zipfile.ZipFile(zip_file, 'r') as z:
                    for fichiers in z.namelist():
                        fichier = z.open(fichiers, 'r')
                        c.parse(fichier, bdd='ris')
                        c.add(project=project, corpus=corpus, user=user, ids=ids)

        except Exception as e:
            print(e)

    elif source.database == "Pubmed":
        try:
            print("PubMed DB detected")
            c = Pubmed()
            if zipfile.is_zipfile(zip_file):
                with zipfile.ZipFile(zip_file, 'r') as z:
                    for fichiers in z.namelist():
                        fichier = z.open(fichiers, 'r')
                        c.parse(fichier)
                        c.ajouter(project=project, corpus=corpus, user=user, ids=ids)

        except Exception as e:
            print(e)
    else:
        print("Corpus not detected")


