from node.models import NodeType
#NodeType.objects.all().delete()
nodeTypeRoot = NodeType(name="Root")
nodeTypeRoot.save()
nodeTypeProject = NodeType(name="Project")
nodeTypeProject.save()
nodeTypeDocument = NodeType(name="Document")
nodeTypeDocument.save()


from node.models import Language
import pycountry
for lang in pycountry.languages:
    try:
        Language(iso2=lang.alpha2, iso3=lang.terminology, fullname=lang.name).save()
    except:
        pass
