from admin.env import *
from gargantext_web.db import *
from gargantext_web.db import get_or_create_node

db, cursor = get_cursor()

def create_corpus(corpus_name, project_id=None, project_name=None, user_id=None):
    if project_name is not None and project_id is None:
        project_id = session.query(Node).filter(Node.name==project_name).first().id

    new_corpus = Node(name=corpus_name, parent_id=project_id, type_id=cache.NodeType['Corpus'].id,user_id=user_id)
    session.add(new_corpus)
    session.commit()
    return(new_corpus.id)


def copy_corpus(from_id=None, to_id=None, title=None):
    '''
    Copy corpus from_id to corpus with to_id
    TODO : guards
    '''
    
    corpus = session.query(Node).filter(Node.id==from_id).first()
    group_id = get_or_create_node(nodetype='Group', corpus=corpus).id
    print( [from_id, cache.NodeType['Document'].id, 'journal', group_id, title, to_id] )
    cursor.execute('''
    CREATE TEMPORARY TABLE node_node__tmp AS
      SELECT 
        n.id,
        n.parent_id,
        n.user_id,
        n.type_id,
        n.name,
        n.language_id,
        n.date,
        n.hyperdata
        
        FROM node_node AS n
        INNER JOIN node_node_hyperdata AS nh ON nh.node_id = n.id
        INNER JOIN node_hyperdata AS h ON h.id = nh.hyperdata_id

        INNER JOIN node_ngram AS ng ON ng.terms = nh.value_string
        INNER JOIN node_nodengramngram AS nnn ON nnn.ngramx_id = ng.id
        INNER JOIN node_ngram AS ng2 ON ng2.id = nnn.ngramy_id

        WHERE n.parent_id = %d
        AND n.type_id = %d
        AND h.name = \'%s\'
        AND nnn.node_id = %d
        AND ng2.terms = \'%s\'
        -- limit 100
        ;
        

    UPDATE node_node__tmp SET parent_id = %d ;
    ALTER TABLE node_node__tmp ADD COLUMN id_new INTEGER;

    with upd as 
    (update node_node__tmp set id_new = nextval(pg_get_serial_sequence('node_node','id')) returning id, id_new) 
        INSERT INTO node_node (id, parent_id, user_id, type_id, name, language_id, date, hyperdata)
        SELECT
        upd.id_new,
        n.parent_id,
        n.user_id,
        n.type_id,
        n.name,
        n.language_id,
        n.date,
        n.hyperdata
        FROM node_node__tmp AS n
        INNER JOIN upd ON upd.id = n.id
    ;

    -- check if copy is ok
    --SELECT n.name, nt.name
    --FROM node_node__tmp AS nt
    --INNER JOIN node_node AS n ON n.id = nt.id_new
    --;

    CREATE TEMPORARY TABLE node_node_ngram__tmp AS
        SELECT nn.id, nn.node_id, nn.ngram_id, nn.weight
        FROM node_node_ngram AS nn
        INNER JOIN node_node__tmp AS nt ON nt.id = nn.node_id ;

    ALTER TABLE node_node_ngram__tmp ADD COLUMN node_id_new INTEGER;

    UPDATE node_node_ngram__tmp set node_id_new = nt.id_new 
    FROM node_node__tmp as nt 
    WHERE node_id = nt.id;

    insert INTO node_node_ngram (node_id, ngram_id, weight) 
    SELECT node_id_new, ngram_id, weight
    FROM node_node_ngram__tmp;

    -- HYPERDATA
    CREATE TEMPORARY TABLE node_node_hyperdata__tmp AS
        SELECT 
        nh.id,
        nh.node_id,
        nh.hyperdata_id,
        nh.value_int,
        nh.value_float,
        nh.value_string,
        nh.value_datetime,
        nh.value_text
        FROM node_node_hyperdata AS nh
        INNER JOIN node_node__tmp AS nt ON nt.id = nh.node_id
        ;

    ALTER TABLE node_node_hyperdata__tmp ADD COLUMN node_id_new INTEGER;

    UPDATE node_node_hyperdata__tmp set node_id_new = nt.id_new 
    FROM node_node__tmp as nt 
    WHERE node_id = nt.id;

    insert INTO node_node_hyperdata (node_id, hyperdata_id, value_int, value_float, value_string, value_datetime, value_text) 
        SELECT 
        nh.node_id_new,
        nh.hyperdata_id,
        nh.value_int,
        nh.value_float,
        nh.value_string,
        nh.value_datetime,
        nh.value_text
        FROM node_node_hyperdata__tmp as nh;
    ''' % (from_id, cache.NodeType['Document'].id, 'journal', group_id, title, to_id)
    
    )


#
#user    = session.query(User).filter(User.username=="alexandre").first()
#project = session.query(Node).filter(Node.id == 272926).first()
#
## title = "test"
#corpus_id = create_corpus(title, project_id=project.id, user_id=user.id)
#print(corpus_id)
##copy_corpus(from_id=272927, to_id=corpus_id, title=title)




