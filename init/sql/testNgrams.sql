select nn.ngram_id from node_node_ngram as nn 
    JOIN node_node as n on nn.node_id = n.id 
    JOIN node_ngram as ng ON ng.id = nn.ngram_id
    JOIN node_node_ngram as nng ON nng.ngram_id = nn.ngram_id
    JOIN node_node as nodeList on nodeList.id = nn.node_id
    JOIN node_nodetype as typ on typ.id = nodeList.type_id

    WHERE n.parent_id = 1452569
    AND ng.terms = 'moral support'
    AND typ.name = 'MiamList'
    GROUP BY nn.ngram_id
    
    ;

