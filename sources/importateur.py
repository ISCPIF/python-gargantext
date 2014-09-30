
# import Celery here

from sources.europresse import Europresse
#from sources.isi import Isi

import zipfile

def importer(source, language, zip_file, project=None, corpus=None, user=None):
    if source.database == "Europresse":
        try:
            c = Europresse()
            if zipfile.is_zipfile(zip_file):
                with zipfile.ZipFile(zip_file, 'r') as z:
                    for fichiers in z.namelist():
                        fichier = z.open(fichiers, 'r')
                        c.parse(fichier)
                        c.ajouter(project=project, corpus=corpus, user=user)

        except Exception as e:
            print(e)
    elif source.database == "Isi":
        pass


