
# Definitions and notation for the documentation (!= python notation)

## Node

The table (nodes) is a list of nodes: [Node]

Each Node has:
- a typename
- a parent_id
- a name


### Each Node has a parent_id

Node A
├── Node B
└── Node C

If Node A is Parent of Node B and Node C
then NodeA.id == NodeB.parent_id == NodeC.parent_id.

### Each Node has a typename

Notation: Node[foo](bar) is a Node of typename "foo" and with name "bar".

Then:
    - Then Node[project] is a project.
    - Then Node[corpus] is a corpus.
    - Then Node[document] is a document.


### Each Node as a typename and a parent


Node[user](name)
├── Node[project](myProject1)
│   ├── Node[corpus](myCorpus1)
│   ├── Node[corpus](myCorpus2)
│   └── Node[corpus](myCorpus3)
└── Node[project](myProject2)


/!\ 3 way to manage rights of the Node:
    1) Then Node[User] is a folder containing all User projects and corpus and
documents (i.e. Node[user] is the parent_id of the children).
    2) Each node as a user_id (mainly used today)
    3) Right management for the groups (implemented already but not
    used since not connected to the frontend).


## Global Parameters

Global User is Gargantua (Node with typename User).
This node is the parent of the others Nodes for parameters.

Node[user](gargantua) (gargantua.id == Node[user].user_id)
├── Node[TFIDF-Global](global) : without group
│   ├── Node[tfidf](database1)
│   ├── Node[tfidf](database2)
│   └── Node[tfidf](database2)
└── Node[anotherMetric](global)



## NodeNgram

NodeNgram is a relation of a Node with a ngram:
    - document and ngrams
    - metrics  and ngrams (position of the node metrics indicates the
      context)




# Community Parameters


# User Parameters



