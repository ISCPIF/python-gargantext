
# import Celery here

from sources.europresse import Europresse
#from sources.isi import Isi

import zipfile

def importer(source, language, zip_file):
    if source.database == "Europresse":
        try:
            c = Europresse()
            if zipfile.is_zipfile(zip_file):
                with zipfile.ZipFile(zip_file, 'r') as z:
                    for f in z.namelist():
                        i = z.open(f, 'r')
                        for l in i.readline():
                            print(l)
                        #c.importer(MEDIA_ROOT + "/" + str(f))

#                    for article in c:
#                        print(article['title'])
        except Exception as e:
            print(e)
    elif source.database == "Isi":
        pass


