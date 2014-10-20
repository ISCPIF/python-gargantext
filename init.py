from node.models import NodeType

#NodeType.objects.all().delete()
NodeType(name="Root").save()
NodeType(name="Project").save()
NodeType(name="Corpus").save()
NodeType(name="Document").save()

from node.models import DatabaseType
for bdd in ['Europresse', 'PubMed', 'Web Of Science (WOS), ISI format']:
    DatabaseType(name=bdd).save()

from node.models import Language
import pycountry
for iso in ['fr', 'en', ]:
    lang = pycountry.languages.get(alpha2=iso)
    Language(iso2=lang.alpha2, iso3=lang.terminology, fullname=lang.name, implemented=1).save()
