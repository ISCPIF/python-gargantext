from gargantext.util.db import *
from gargantext.util.db_cache import *
from gargantext.constants import *

from gargantext.models.ngrams import Ngram, NodeNgram,\
        NodeNodeNgram, NodeNgramNgram


from sqlalchemy.sql import func
from sqlalchemy import desc, asc, or_, and_, Date, cast, select
from sqlalchemy import literal_column
from sqlalchemy.orm import aliased

from gargantext.util.toolchain.ngram_tools import insert_ngrams
import csv

def compute_mapList(corpus_id,limit=500,n=1, session=None):
    '''
    According to Specificities and stoplist,
    '''
    
 
    monograms_part = 0.005
    monograms_limit = round(limit * monograms_part)
    multigrams_limit = limit - monograms_limit

    #dbg = DebugTime('Corpus #%d - computing Miam' % corpus.id)
    
    list_main_id  = session.query(Node.id).filter(
            Node.typename  == "MAINLIST",
            Node.parent_id == corpus_id).first()

    list_stop_id  = session.query(Node.id).filter(
            Node.typename  == "STOPLIST",
            Node.parent_id == corpus_id).first()
    
    list_group_id = session.query(Node.id).filter(
            Node.typename  == "GROUPLIST",
            Node.parent_id == corpus_id).first()

    score_spec_id = session.query(Node.id).filter(
            Node.typename  == "SPECIFICITY",
            Node.parent_id == corpus_id).first()


    ListMain=aliased(NodeNgram)
    ListStop=aliased(NodeNgram)
    ListGroup=aliased(NodeNgramNgram)
    
    ScoreSpec=aliased(NodeNodeNgram)
    
    # FIXME outerjoin does not work with current SqlAlchemy
    # lines below the query do the job but it can be improved
    query = (session.query(ScoreSpec.ngram_id, ScoreSpec.score)
                .join(ListMain, ScoreSpec.ngram_id == ListMain.ngram_id)
                .join(Ngram, Ngram.id == ScoreSpec.ngram_id)
                #.outerjoin(ListGroup, Group.ngramy_id == ScoreSpec.ngram_id)
                #.outerjoin(ListStop, Stop.ngram_id == ScoreSpec.ngram_id)
                .filter(ListMain.node_id == list_main_id)
                #.filter(ListGroup.node_id == list_group_id)
                #.filter(ListStop.node_id == list_stop_id)
                .filter(ScoreSpec.nodex_id == score_spec_id)
            )

    top_monograms = (query
                .filter(Ngram.n == 1)
                .order_by(desc(ScoreSpec.score))
                .limit(monograms_limit)
               )
    
    top_multigrams = (query
                .filter(Ngram.n >= 2)
                .order_by(desc(ScoreSpec.score))
                .limit(multigrams_limit)
               )
    
    stop_ngrams = (session.query(NodeNgram.ngram_id)
                         .filter(NodeNgram.node_id == list_stop_id)
                         .all()
                 )

    grouped_ngrams = (session.query(NodeNgramNgram.ngramy_id)
                             .filter(NodeNgramNgram.node_id == list_group_id)
                             .all()
                    )
    
    
    
    list_map_id = session.query(Node.id).filter(
        Node.parent_id==corpus_id,
        Node.typename == "MAPLIST"
        ).first()
    
    if list_map_id == None:
        corpus = cache.Node[corpus_id]
        user_id = corpus.user_id
        list_map = Node(name="MAPLIST", parent_id=corpus_id, user_id=user_id, typename="MAPLIST")
        session.add(list_map)
        session.commit()
        list_map_id = list_map.id

    
    session.query(NodeNgram).filter(NodeNgram.node_id==list_map_id).delete()
    session.commit()
    
    data = zip(
        [list_map_id for i in range(1,limit)]
        , [n[0] for n in list(top_multigrams) + list(top_monograms)
                if (n[0],) not in list(stop_ngrams) 
            ]
        , [1 for i in range(1,limit)]
    )
    #print([d for d in data])
    bulk_insert(NodeNgram, ['node_id', 'ngram_id', 'weight'], [d for d in data])

    dbg.show('MapList computed')

