
# Definitions and notation for the documentation (!= python notation)

## Node

The table (nodes) is a list of nodes: `[Node]`

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

Notation: `Node["FOO"]("bar")` is a Node of typename "FOO" and with name "bar".

Then:

- Then Node[PROJECT] is a project.
- Then Node[CORPUS] is a corpus.
- Then Node[DOCUMENT] is a document.

The syntax of the Node here do not follow exactly Python documentation
(for clarity and to begin with): in Python code, typenames are strings
represented as UPPERCASE strings (eg. "PROJECT").

### Each Node as a typename and a parent

    Node[USER](name)
    ├── Node[PROJECT](myProject1)
    │   ├── Node[CORPUS](myCorpus1)
    │   ├── Node[CORPUS](myCorpus2)
    │   └── Node[CORPUS](myCorpus3)
    └── Node[PROJECT](myProject2)

/!\\ 3 ways to manage rights of the Node:

1. Then Node[User] is a folder containing all User projects and corpus and
   documents (i.e. Node[user] is the parent_id of the children).
2. Each node as a user_id (mainly used today)
3. Right management for the groups (implemented already but not
   used since not connected to the frontend).


## Global Parameters

Global User is Gargantua (Node with typename user).
This node is the parent of the other nodes for parameters.

    Node[USER](gargantua) (gargantua.id == Node[USER].user_id)
    ├── Node[TFIDF-Global](global) : without group
    │   ├── Node[TFIDF](database1)
    │   ├── Node[TFIDF](database2)
    │   └── Node[TFIDF](database3)
    └── Node[ANOTHERMETRIC](global)


[//]: # (Are there any plans to add user wide or project wide parameters or metrics?  For example TFIDF nodes related to a normal user -- ie. not Gargantua?)

Yes we can in the futur (but we have others priorities before.

[//]: # (What is the purpose of the 3 child nodes of Node[TFIDF-Global]?  Are they TFIDF metrics related to databases 1, 2 and 3? If so, shouldn't they be children of related CORPUS nodes?)

Node placement in the tree indicates the context of the metric: the
Metrics Node has parent the corpus Node to indicate the context of the
metrics.

Answer:

    Node[USER](foo)
    Node[USER](bar)
    ├── Node[PROJECT](project1)
    │   ├── Node[CORPUS](corpus1)
    │   │   ├── Node[DOCUMENT](doc1)
    │   │   ├── Node[DOCUMENT](doc2)
    │   │   └── Node[TFIDF-global](name of the metrics)
    │   ├── Node[CORPUS](corpus2)
    │   └── Node[CORPUS](corpus3)
    └── Node[PROJECT](project2)



## NodeNgram

NodeNgram is a relation of a Node with a ngram:

- documents and ngrams
- metrics  and ngrams (position of the node metrics indicates the
  context)



# Community Parameters


# User Parameters



