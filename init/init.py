from node.models import NodeType
from django.contrib.auth.models import User

user = User.objects.get(username="alexandre")
#NodeType.objects.all().delete()
type_root = NodeType(name="Root")
type_root.save()

type_project = NodeType(name="Project")
type_project.save()

NodeType(name="Corpus").save()
NodeType(name="Document").save()

from node.models import Project
Project(name="Projet sur les abeilles", user=user, type=type_project).save()

from node.models import ResourceType
for bdd in ['Europresse', 'PubMed', 'Web Of Science (WOS), ISI format']:
    ResourceType(name=bdd).save()

from node.models import Language
import pycountry
for iso in ['fr', 'en', ]:
    lang = pycountry.languages.get(alpha2=iso)
    Language(iso2=lang.alpha2, iso3=lang.terminology, fullname=lang.name, implemented=1).save()
