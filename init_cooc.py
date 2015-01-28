# Without this, we couldn't use the Django environment

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gargantext_web.settings")
os.environ.setdefault("DJANGO_HSTORE_GLOBAL_REGISTER", "False")


# We're gonna use all the models!

from node.models import User, NodeType, Node


user = User.objects.get(username = 'contro2015.lait')

# Reset: all data

try:
    typeDoc     = NodeType.objects.get(name='Cooccurrence')
except Exception as error:
    print(error)

Node.objects.filter(user=user, type=typeDoc).all().delete()

exit()
