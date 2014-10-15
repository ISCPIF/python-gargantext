# coding: utf-8


from node.models import Node, NodeType
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


# In[ ]:

Node.objects.all().delete()
User.objects.filter(username__startswith = "User #").delete()

t0 = time()
for userIndex in range(100):
    userName = 'User #%d' % (userIndex, )
    user = User(username=userName)
    user.save()
    rootNode = Node.add_root(name=userName, type_id=nodeTypeRoot.pk, user_id=user.id)
    print(userName)
    for projectIndex in range(50):
        projectName = 'Project #%d-%d' % (userIndex, projectIndex, )
        projectNode = Node(name=projectName, type_id=nodeTypeProject.pk, user_id=user.id)
        rootNode.add_child(instance=projectNode)
        documents = [
            {"data": {"name":'Document #%d-%d-%d' % (userIndex, projectIndex, documentIndex, ), "type_id":nodeTypeDocument.pk, "user_id":user.id}}
            for documentIndex in range(10000)
        ]
        Node.load_bulk(documents, projectNode)
print(time() - t0)


# In[37]:

for node in Node.objects.all():
    print(node.name)


# 
