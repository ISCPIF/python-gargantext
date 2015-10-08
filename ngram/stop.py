# Without this, we couldn't use the Django environment
#from admin.env import *
#from ngram.stemLem import *

from admin.utils import PrintException

from gargantext_web.db import NodeNgram,NodeNodeNgram
from gargantext_web.db import get_or_create_node, session

from sqlalchemy.sql import func
from sqlalchemy import desc, asc, or_, and_, Date, cast, select
from sqlalchemy import literal_column
from sqlalchemy.orm import aliased




def computeStop(corpus,size=100):
    '''
    do some statitics on all stop lists of database of the same type
    '''
    node_stop = get_or_create_node(nodetype='StopList', corpus=corpus)
    Stop=aliased(NodeNgram)

    top_spec = (session.query(NodeNodeNgram.ngram_id, NodeNodeNgram.score)
                .outerjoin(Stop, Stop.ngram_id == NodeNodeNgram.ngram_id)
                .filter(NodeNodeNgram.nodex_id==node_spec.id)
                .filter(Stop.node_id==node_stop.id)
                .order_by(desc(NodeNodeNgram.score))
                .limit(size)
                )

    node_miam = get_or_create_node(nodetype='MiamList', corpus=corpus)
    session.query(NodeNgram).filter(NodeNgram.node_id==node_miam.id).delete()

    data = zip(
        [node_miam.id for i in range(1,size)]
        , [1 for i in range(1,size)]
        , [n[0] for n in top_spec]
    )
    #print([d for d in data])
    bulk_insert(NodeNgram, ['node_id', 'ngram_id', 'weight'], [d for d in data])


#corpus=session.query(Node).filter(Node.id==244250).first()
#computeMiam(corpus)




