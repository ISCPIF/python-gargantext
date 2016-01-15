
from gargantext_web.db import get_session, cache, get_cursor
from gargantext_web.db import Node, NodeNgram, NodeNodeNgram
from gargantext_web.db import get_or_create_node
from admin.utils import DebugTime

def compute_occs(corpus):
    '''
    compute_occs :: Corpus -> IO ()

    '''
    sessionToRemove = False
    if session is None:
        session = get_session()
        sessionToRemove = True
    
    dbg = DebugTime('Corpus #%d - OCCURRENCES' % corpus.id)
    dbg.show('Calculate occurrences')
    occs_node = get_or_create_node(nodetype='Occurrences', corpus=corpus)
    
    #print(occs_node.id)

    (session.query(NodeNodeNgram)
            .filter(NodeNodeNgram.nodex_id==occs_node.id).delete()
            )
    session.commit()

    db, cursor = get_cursor()
    cursor.execute('''
        INSERT INTO
            %s (nodex_id, nodey_id, ngram_id, score)
        SELECT
            %d AS nodex_id,
            %d AS nodey_id,
            nodengram.ngram_id AS ngram_id,
            SUM(nodengram.weight) AS score
        FROM
            %s AS nodengram
        INNER JOIN
            %s AS node     ON nodengram.node_id = node.id
        WHERE
            node.parent_id = %d
            AND
            node.type_id = %d
        GROUP BY
            nodengram.ngram_id
            

    ''' % (   NodeNodeNgram.__table__.name
            , occs_node.id, corpus.id
            , NodeNgram.__table__.name
            , Node.__table__.name
            , corpus.id
            , cache.NodeType['Document'].id
            )
    )
    db.commit()
    if sessionToRemove: session.remove()


    #data = session.query(NodeNodeNgram).filter(NodeNodeNgram.nodex_id==occs_node.id).all()
    #print([n for n in data])
