# coding: utf-8

from django.db import transaction
from models import Node, NodeType
from django.contrib.auth.models import User

from time import time

print(time())


# In[9]:

NodeType.objects.all().delete()
nodeTypeRoot = NodeType(name="Root")
nodeTypeRoot.save()
nodeTypeProject = NodeType(name="Project")
nodeTypeProject.save()
nodeTypeDocument = NodeType(name="Document")
nodeTypeDocument.save()

#number_userIndex = 100
#number_projectIndex = 50
#number_documentIndex = 10000

number_userIndex = 10
number_projectIndex = 5
number_documentIndex = 100


# In[ ]:

Node.objects.all().delete()
User.objects.filter(username__startswith = "User #").delete()

t0 = time()


with transaction.atomic():
    for userIndex in range(number_userIndex):
        userName = 'User #%d' % (userIndex, )
        user = User(username=userName)
        user.save()
        rootNode = Node.add_root(name=userName, type_id=nodeTypeRoot.pk, user_id=user.id)
        print(userName)
        for projectIndex in range(number_projectIndex):
            projectName = 'Project #%d-%d' % (userIndex, projectIndex, )
            projectNode = Node(name=projectName, type_id=nodeTypeProject.pk, user_id=user.id)
            rootNode.add_child(instance=projectNode)
            documents = [
                {"data": {"name":'Document #%d-%d-%d' % (userIndex, projectIndex, documentIndex, ), "type_id":nodeTypeDocument.pk, "user_id":user.id}}
                for documentIndex in range(number_documentIndex)
            ]
            Node.load_bulk(documents, projectNode)
print(time() - t0)


# In[37]:

for node in Node.objects.all():
    print(node.name)


# 
