from node.models import Language, ResourceType, Resource, \
        Node, NodeType, Node_Resource, Project, Corpus, \
        Node_Ngram, NodeNgramNgram

from collections import defaultdict
from django.db import connection, transaction

def create_blacklist(user, corpus):
    pass

def create_synonymes(user, corpus):
    pass

def create_whitelist(user, corpus):
    cursor = connection.cursor()
    
    try:
        whitelist_type = NodeType.objects.get(name='WhiteList')
        blacklist_type = NodeType.objects.get(name='BlackList')
        type_document  = NodeType.objects.get(name='Document')
    except:
        whitelist_type = NodeType(name='WhiteList')
        whitelist_type.save()
    
        blacklist_type = NodeType(name='BlackList')
        blacklist_type.save()

    white_list = Node.objects.create(name='WhiteList Corpus ' + str(corpus.id), user=user, parent=corpus, type=whitelist_type)
    black_list = Node.objects.create(name='BlackList Corpus ' + str(corpus.id), user=user, parent=corpus, type=blacklist_type)

    # delete avant pour éviter les doublons
#    try:
#        Node_Ngram.objects.filter(node=white_list).all().delete()
#    except:
#        print('First time we compute cooc')
#
    query_whitelist = """
        INSERT INTO node_node_ngram (node_id, ngram_id, weight)
        SELECT
            %d,
            ngX.id,
            COUNT(*) AS occurrences
        FROM
            node_node AS n
        INNER JOIN
            node_node_ngram AS nngX ON nngX.node_id = n.id
        INNER JOIN
            node_ngram AS ngX ON ngX.id = nngX.ngram_id
        WHERE
            n.parent_id = %d
        AND
            n.type_id = %d
        AND
            ngX.n >= 1

        GROUP BY
            ngX.id
        Having
            COUNT(*) >= 1
        ORDER BY
            occurrences DESC
        LIMIT
            100
        ;
    """  % (white_list.id, corpus.id, type_document.id)

    cursor.execute(query_whitelist)

    return white_list

#def create_cooc(user, corpus, whitelist, blacklist, synonymes):
def create_cooc(user=None, corpus=None, whitelist=None, size=200):
    cursor = connection.cursor()

    try:
        cooc_type  = NodeType.objects.get(name='Cooccurrence')
    except:
        cooc_type = NodeType(name='Cooccurrence')
        cooc_type.save()
    # pour les tests on supprime les cooc
    Node.objects.filter(type=cooc_type, parent=corpus).delete()

    cooc = Node.objects.create(user=user,\
                           parent=corpus,\
                           type=cooc_type,\
                           name="Cooccurrences corpus " + str(corpus.pk))

    query_cooc = """
    INSERT INTO node_nodengramngram (node_id, "ngramx_id", "ngramy_id", score)
        SELECT
        %d as node_id,
        ngX.id,
        ngY.id,
        COUNT(*) AS score
    FROM
        node_node AS n  -- the nodes who are direct children of the corpus
        
    INNER JOIN
        node_node_ngram AS nngX ON nngX.node_id = n.id  --  list of ngrams contained in the node
    INNER JOIN
        node_node_ngram AS whitelistX ON whitelistX.ngram_id = nngX.ngram_id -- list of ngrams contained in the whitelist and in the node
    INNER JOIN
        node_ngram AS ngX ON ngX.id = whitelistX.ngram_id -- ngrams which are in both
        
    INNER JOIN
        node_node_ngram AS nngY ON nngY.node_id = n.id
    INNER JOIN
        node_node_ngram AS whitelistY ON whitelistY.ngram_id = nngY.ngram_id
    INNER JOIN
        node_ngram AS ngY ON ngY.id = whitelistY.ngram_id
        
    WHERE
        n.parent_id = %s
    AND
        whitelistX.node_id = %s
    AND
        whitelistY.node_id = %s
    AND
        nngX.ngram_id < nngY.ngram_id   --  so we only get distinct pairs of ngrams
        
    GROUP BY
        ngX.id,
        ngX.terms,
        ngY.id,
        ngY.terms
    
    ORDER BY
        score DESC
    LIMIT
        %d
    """ % (cooc.pk, corpus.id, whitelist.id, whitelist.id, size)

    cursor.execute(query_cooc)
    return cooc



