
from admin.env import *
from gargantext_web.db import session, cache, get_or_create_node
from gargantext_web.db import Node, NodeHyperdata, Hyperdata, Ngram, NodeNgram, NodeNgramNgram, NodeHyperdataNgram
from sqlalchemy import func, alias, asc, desc
import sqlalchemy as sa
from sqlalchemy.orm import aliased

from ngram.group import compute_groups, getStemmer

# corpus = Corpus(272)
corpus_id = 540420
corpus = session.query(Node).filter(Node.id==corpus_id).first()
#group = get_or_create_node(corpus=corpus, nodetype="Group")

stop_id = get_or_create_node(nodetype='StopList',corpus=corpus).id
miam_id = get_or_create_node(nodetype='MiamList',corpus=corpus).id

somme = sa.func.count(NodeNgram.weight)
ngrams = (session.query(Ngram.id, Ngram.terms, somme )
        .join(NodeNgram, NodeNgram.ngram_id == Ngram.id)
        .join(Node, Node.id == NodeNgram.node_id)
        .filter(Node.parent_id==corpus_id, Node.type_id==cache.NodeType['Document'].id)
        .group_by(Ngram.id)
        .order_by(desc(somme))
        .limit(100000)
        )

stops = (session.query(Ngram.id, Ngram.terms)
                .join(NodeNgram, NodeNgram.ngram_id == Ngram.id)
                .filter(NodeNgram.node_id == stop_id)
                .all()
                )

miams = (session.query(Ngram.id, Ngram.terms, somme)
                .join(NodeNgram, NodeNgram.ngram_id == Ngram.id)
                .filter(NodeNgram.node_id == miam_id)
                .group_by(Ngram.id, Ngram.terms)
                .order_by(desc(somme))
                .all()
                )

stemmer = getStemmer(corpus)

ws = ['honeybee', 'honeybees']

print(stemmer(ws[0]) == stemmer(ws[1]))

#
#for n in miams:
#    if n[1] == 'bees':
#        print("!" * 30)
#        print(n)
#        print("-" * 30)
#    else:
#        print(n)
#
