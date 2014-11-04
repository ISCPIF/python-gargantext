
# coding: utf-8

# In[1]:

from node.models import Node, NodeType,                        Project, Corpus, Document,                        Ngram, Node_Ngram,                        User, Language, ResourceType


# In[2]:

import pycountry

for language in pycountry.languages:
    try:
        implemented = 1 if language.alpha2 in ['en', 'fr'] else 0
        Language(iso2=language.alpha2, iso3=language.terminology, fullname=language.name, implemented=implemented).save()
    except:
        pass


# In[3]:

english = Language.objects.get(iso2='en')
french  = Language.objects.get(iso2='fr')


# In[4]:

try:
    me = User.objects.get(username='alexandre')
except:
    me = User(username='alexandre')
    me.save()


# In[5]:

try:
    typeProject = NodeType.objects.get(name='Project')
except Exception as error:
    print(error)
    typeProject = NodeType(name='Project')
    typeProject.save()  

try:
    typeCorpus  = NodeType.objects.get(name='Corpus')
except Exception as error:
    print(error)
    typeCorpus  = NodeType(name='Corpus')
    typeCorpus.save()
    
try:
    typeDoc     = NodeType.objects.get(name='Document')
except Exception as error:
    print(error)
    typeDoc     = NodeType(name='Document')
    typeDoc.save()


# In[6]:

try:
    typePubmed = ResourceType.objects.get(name='pubmed')
    typeIsi    = ResourceType.objects.get(name='isi')
    typeRis    = ResourceType.objects.get(name='ris')
    typePresse = ResourceType.objects.get(name='europress')

except Exception as error:
    print(error)
    
    typePubmed = ResourceType(name='pubmed')
    typePubmed.save()  
    
    typeIsi    = ResourceType(name='isi')
    typeIsi.save()
    
    typeRis    = ResourceType(name='ris')
    typeRis.save()
    
    typePresse = ResourceType(name='europress')
    typePresse.save()


# In[10]:

Node.objects.all().delete()


# In[8]:

try:
    project = Node.objects.get(name='Bees project')
except:
    project = Node(name='Bees project', type=typeProject, user=me)
    project.save()


# ### Pubmed

# In[18]:

try:
    corpus_pubmed = Node.objects.get(name='PubMed corpus')
except:
    corpus_pubmed = Node(parent=project, name='PubMed corpus', type=typeCorpus, user=me)
    corpus_pubmed.save()


# In[19]:

corpus_pubmed.add_resource(file='/srv/gargantext_lib/data_samples/pubmedBig.zip', type=typePubmed)


# In[20]:

#corpus_abeille.add_resource(file='/srv/gargantext_lib/data_samples/pubmed.zip', type=typePubmed)


# In[21]:

corpus_pubmed.parse_resources()
corpus_pubmed.children.count()


# In[22]:

corpus_pubmed.children.all().extract_ngrams(['title',])
Node_Ngram.objects.filter(node=corpus_pubmed.children.all()[0]).count()


# ### RIS

# In[9]:

try:
    corpus_ris = Node.objects.get(name='RIS corpus')
except:
    corpus_ris = Node(parent=project, name='RIS corpus', type=typeCorpus, user=me)
    corpus_ris.save()


# In[10]:

corpus_ris.add_resource(file='/srv/gargantext_lib/data_samples/risUnix.zip', type=typeRis)


# In[15]:

corpus_ris.parse_resources()


# In[16]:

corpus_ris.children.count()


# In[40]:

corpus_ris.children.all()


# In[28]:

corpus_ris.name = "ZOTERO CORPUS (CIRDEM)"
corpus_ris.save()


# ### Science

# In[23]:

try:
    science = Node.objects.get(name='WOS corpus')
except:
    science = Node(parent=project, name='WOS corpus', type=typeCorpus, user=me)
    science.save()


# In[24]:

science.add_resource(file='/srv/gargantext_lib/data_samples/isi.zip', type=typeIsi)
science.parse_resources()
science.children.count()


# In[25]:

science.children.last().metadata


# In[26]:

science.children.all().extract_ngrams(['abstract',])
Node_Ngram.objects.filter(node=science.children.all()[0]).count()


# ### Press

# In[29]:

try:
    presse = Node.objects.get(name='Presse corpus')
except:
    presse = Node(parent=project, name='Presse corpus', type=typeCorpus, user=me)
    presse.save()


# In[30]:

presse.add_resource(file='/srv/gargantext_lib/data_samples/html/html_french.zip', type=typePresse)


# In[31]:

presse.parse_resources()


# In[32]:

presse.children.count()


# In[33]:

presse.children.all().extract_ngrams(['title',])


# In[34]:

project.children.all()


# In[37]:

corpus.children.all()


# In[46]:

liste_ordered = collections.OrderedDict(sorted(liste.items()), key=lambda t: t[1])


# In[52]:

#liste_ordered


# # Création des Listes

# In[57]:

import collections


# In[58]:

liste = collections.defaultdict(int)


# In[59]:

try:
    whitelist_type  = NodeType.objects.get(name='WhiteList')
    blacklist_type = NodeType.objects.get(name='BlackList')
except:
    whitelist_type = NodeType(name='WhiteList')
    whitelist_type.save()
    
    blacklist_type = NodeType(name='BlackList')
    blacklist_type.save()

white_node = Node.objects.create(name='WhiteList Pubmed', user=me, parent=corpus_pubmed, type=whitelist_type)
black_node = Node.objects.create(name='BlackList Pubmed', user=me, parent=corpus_pubmed, type=blacklist_type)


# In[60]:

Node_Ngram.objects.filter(node=white_node).count()


# # Création de la white list

# In[61]:

with transaction.atomic():
    for node in corpus_pubmed.children.all():
        for node_ngram in Node_Ngram.objects.filter(node=node):
            if node_ngram.ngram.n > 1:
                #liste[node_ngram.ngram.terms] += node_ngram.weight
                Node_Ngram.objects.create(node=white_node, ngram=node_ngram.ngram, weight=1)


# In[62]:

white_node.pk


# In[63]:

Node_Ngram.objects.filter(node=white_node).count()


# # Création de la black list

# In[64]:

with transaction.atomic():
    for node_ngram_object in Node_Ngram.objects.all()[101:150]:
        Node_Ngram.objects.create(node=black_node, ngram=node_ngram_object.ngram, occurences=1)


# In[12]:

Node_Ngram.objects.filter(node=black_node)


# # Création des synonymes

# In[13]:

syno_type  = NodeType.objects.get(name='Synonyme')
syno_node = Node.objects.create(name='Syno Pubmed',
                                user=user, 
                                parent=corpus, 
                                type=syno_type)


# In[23]:

synonyme1, synonyme2 = Node_Ngram.objects.filter(node=white_node)[3:5]


# In[24]:

NodeNgramNgram.objects.create(node=syno_node, ngramX=synonyme1.ngram, ngramY=synonyme2.ngram)


# # Cooccurrence

# In[65]:

white_node.children.count()


# In[66]:

black_node.pk


# In[67]:

try:
    cooc_type  = NodeType.objects.get(name='Cooccurrence')
except:
    cooc_type = NodeType(name='Cooccurrence')
    cooc_type.save()


# In[68]:

cooc = Node.objects.create(user=me,                           parent=corpus_pubmed,                           type=cooc_type,                           name="Cooccurrences calcul Alpha")


# In[69]:

cooc.pk


# In[152]:

white_node.children.all().delete()


# In[70]:

from django.db import connection
cursor = connection.cursor()
# LOCK TABLE documents_ngramtemporary IN EXCLUSIVE MODE;
query_string = """
INSERT INTO node_nodengramngram (node_id, "ngramX_id", "ngramY_id", score)

SELECT 
%d as node_id, x.ngram_id, y.ngram_id, COUNT(*) AS score

FROM
node_node_ngram AS x

INNER JOIN 
node_node_ngram AS y 
ON x.node_id = y.node_id


WHERE
x.id in (select id from node_node_ngram WHERE node_id = %d )
AND
y.id in (select id from node_node_ngram WHERE node_id = %d )
AND
x.ngram_id <> y.ngram_id


GROUP BY
x.ngram_id, y.ngram_id

HAVING count(*) > 1

ORDER BY score

LIMIT 300

             """ % (cooc.pk, white_node.pk, white_node.pk)

cursor.execute(query_string)

try:
    while True:
        row = cursor.fetchone()
        if row is None:
            break
        print(row)
except:
    pass


# In[1]:




# In[45]:




# In[71]:

from copy import copy
import numpy as np
import pandas as pd
import networkx as nx
from collections import defaultdict
from analysis.louvain import *
import matplotlib.pyplot as plt
get_ipython().magic('matplotlib inline')


# In[ ]:

matrix = ""


# In[72]:

matrix = defaultdict(lambda : defaultdict(float))
for cooccurrence in NodeNgramNgram.objects.filter(node=cooc):
    if cooccurrence.score > 1 :
        #print(x.ngramX.terms, x.ngramY.terms)
        matrix[cooccurrence.ngramX.terms][cooccurrence.ngramY.terms] = cooccurrence.score
        matrix[cooccurrence.ngramY.terms][cooccurrence.ngramX.terms] = cooccurrence.score


# In[73]:

df = pd.DataFrame(matrix).T.fillna(0)
x = copy(df.values)


# In[74]:

x = np.where((x.sum(axis=1) > x.shape[0] / 2), 0, x )
x = np.where((x.sum(axis=1) > x.shape[0] / 10), 0, x )


# In[75]:

x = x / x.sum(axis=1)


# In[76]:

matrix_filtered = np.where(x > .4, 1, 0)


# In[77]:

matrix_filtered


# In[78]:

G = nx.from_numpy_matrix(matrix_filtered)
G = nx.relabel_nodes(G, dict(enumerate(df.columns)))


# In[79]:

nx.draw(G, with_labels=True)
plt.show()


# In[80]:

partition = best_partition(G)


# In[ ]:

#partition


# In[81]:

pos = nx.spring_layout(G)


# In[82]:

count = 0.0
node_min = 3
for com in set(partition.values()) :
    count = count + 1
    list_nodes = [nodes for nodes in partition.keys() if partition[nodes] == com]
            
    if len(list_nodes) > node_min:
        nx.draw_networkx_nodes(G, pos, list_nodes, node_size = 20, with_labels=True)#, node_color = str(count / size))
        nx.draw_networkx_edges(G, pos, alpha=0.5)
        plt.title("Clique " + str(count))
                
        for node in list_nodes: 
            print(node)
            plt.show()
            print("-" * 30)


# In[ ]:




# In[ ]:



