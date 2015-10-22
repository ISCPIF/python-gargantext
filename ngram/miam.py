# Without this, we couldn't use the Django environment
#from admin.env import *
#from ngram.stemLem import *

from admin.utils import PrintException,DebugTime

from gargantext_web.db import NodeNgram,NodeNodeNgram,NodeNgramNgram
from gargantext_web.db import get_or_create_node, session, bulk_insert

from sqlalchemy.sql import func
from sqlalchemy import desc, asc, or_, and_, Date, cast, select
from sqlalchemy import literal_column
from sqlalchemy.orm import aliased

from ngram.tools import insert_ngrams
import csv

def compute_miam(corpus,limit=500):
    '''
    According to Specificities and stoplist,
    '''
    dbg = DebugTime('Corpus #%d - computing Miam' % corpus.id)

    node_group = get_or_create_node(nodetype='Group', corpus=corpus)
    node_stop  = get_or_create_node(nodetype='StopList', corpus=corpus)
    node_spec  = get_or_create_node(nodetype='Specificity', corpus=corpus)

    Stop=aliased(NodeNgram)
    Group=aliased(NodeNgramNgram)
    Spec=aliased(NodeNodeNgram)

    top_miam = (session.query(Spec.ngram_id, Spec.score)
                .outerjoin(Group, Group.ngramy_id == Spec.ngram_id)
                .outerjoin(Stop, Stop.ngram_id == Spec.ngram_id)
                .filter(Group.node_id == node_group.id)
                .filter(Stop.node_id == node_stop.id)
                .order_by(desc(Spec.score))
                .limit(limit)
               )
    print([t for t in top_miam])
    node_miam = get_or_create_node(nodetype='MiamList', corpus=corpus)
    session.query(NodeNgram).filter(NodeNgram.node_id==node_miam.id).delete()
    session.commit()

    data = zip(
        [node_miam.id for i in range(1,limit)]
        , [n[0] for n in top_miam]
        , [1 for i in range(1,limit)]
    )
    print([d for d in data])
    bulk_insert(NodeNgram, ['node_id', 'ngram_id', 'weight'], [d for d in data])

    dbg.show('Miam computed')

def insert_miam(corpus, ngrams=None, path_file_csv=None):
    dbg = DebugTime('Corpus #%d - computing Miam' % corpus.id)
    
    node_miam = get_or_create_node(nodetype='MiamList', corpus=corpus)
    session.query(NodeNgram).filter(NodeNgram.node_id==node_miam.id).delete()
    session.commit()
    
    stop_words = set()
    miam_words = set()
    
    if path_file_csv is not None:
        file_csv = open(path_file_csv, "r")
    reader = csv.reader(file_csv, delimiter=',')

    for line in reader:
        word = line[0]
        tag  = line[4]
        if tag == '1':
            miam_words.add((word, 1))
        elif tag == '0':
            stop_words.add((word, 1))
    
    miam_ids = insert_ngrams(miam_words)
    print(miam_ids)
    limit = len(list(miam_words))
    data = zip(
        [node_miam.id for i in range(1,limit)]
        , [miam_ids[n] for n in miam_ids.keys()]
        , [1 for i in range(1,limit)]
    )
    #print([d for d in data])
    bulk_insert(NodeNgram, ['node_id', 'ngram_id', 'weight'], [d for d in data])
    file_csv.close()
    dbg.show('Miam computed')

#corpus = session.query(Node).filter(Node.id==556113).first()
#insert_miam(corpus=corpus, path_file_csv="Thesaurus_tag.csv")



