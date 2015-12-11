select * from node_nodengramngram as nnn 
    JOIN node_node as n on nnn.node_id = n.id 
    JOIN node_ngram as ng ON ng.id = nnn.ngramy_id
    JOIN node_node as nodeList on nodeList.id = nnn.node_id
    JOIN node_nodetype as typ on typ.id = nodeList.type_id

    WHERE n.parent_id = 1452569
    AND ng.terms = 'moral support'
    AND typ.name = 'GroupList'
    
    ;

