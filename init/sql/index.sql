-- Indexing text fields
CREATE INDEX node_node_name ON node_node (name);
CREATE INDEX node_node_metadata_valuetext ON node_node_metadata (value_text);
CREATE INDEX node_ngram_terms ON node_ngram (terms);

-- indexing ALL foreing keys
CREATE INDEX node_ngram__language_id ON node_ngram (language_id);
CREATE INDEX node_node__type_id ON node_node (type_id);
CREATE INDEX node_node__user_id ON node_node (user_id);
CREATE INDEX node_node__language_id ON node_node (language_id);
CREATE INDEX node_node__parent_id ON node_node (parent_id);
CREATE INDEX node_node_metadata__node_id ON node_node_metadata (node_id);
CREATE INDEX node_node_metadata__metadata_id ON node_node_metadata (metadata_id);
CREATE INDEX node_node_ngram__ngram_id ON node_node_ngram (ngram_id);
CREATE INDEX node_node_ngram__node_id ON node_node_ngram (node_id);
CREATE INDEX node_nodengramngram__node_id ON node_nodengramngram (node_id);
CREATE INDEX node_nodengramngram__ngramx_id ON node_nodengramngram (ngramx_id);
CREATE INDEX node_nodengramngram__ngramy_id ON node_nodengramngram (ngramy_id);
CREATE INDEX node_nodenodengram__nodey_id ON node_nodenodengram (nodey_id);
CREATE INDEX node_nodenodengram__ngram_id ON node_nodenodengram (ngram_id);
CREATE INDEX node_nodenodengram__nodex_id ON node_nodenodengram (nodex_id);
CREATE INDEX node_node_resource__node_id ON node_node_resource (node_id);
CREATE INDEX node_node_resource__resource_id ON node_node_resource (resource_id);
CREATE INDEX node_resource__user_id ON node_resource (user_id);
CREATE INDEX node_resource__type_id ON node_resource (type_id);

