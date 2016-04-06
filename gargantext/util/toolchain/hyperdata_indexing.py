from gargantext.util.db import bulk_insert
from gargantext.constants import INDEXED_HYPERDATA
from gargantext.models import NodeHyperdata
from datetime          import datetime

def _nodes_hyperdata_generator(corpus):
    """This method generates columns for insertions in `nodes_hyperdata`.
    In case one of the values is a list, its items are iterated over and
    yielded separately.
    If its a string (eg date) it will be truncated to 255 chars
    """
    for document in corpus.children(typename='DOCUMENT'):
        for keyname, key in INDEXED_HYPERDATA.items():
            if keyname in document.hyperdata:
                values = key['convert_to_db'](document.hyperdata[keyname])
                if not isinstance(values, list):
                    values = [values]
                for value in values:
                    if isinstance(value, (int, )):
                        yield (
                            document.id,
                            key['id'],
                            value,
                            None,
                            None,
                            None,
                            None,
                        )
                    elif isinstance(value, (float, )):
                        yield (
                            document.id,
                            key['id'],
                            None,
                            value,
                            None,
                            None,
                            None,
                        )

                    elif isinstance(value, (datetime, )):
                        yield (
                            document.id,
                            key['id'],
                            None,
                            None,
                            value.strftime("%Y-%m-%d %H:%M:%S"), 
                            # FIXME check timestamp +%Z
                            None,
                            None,
                        )

                    elif isinstance(value, (str, )) :
                        if len(value) < 255 :
                            yield (
                                document.id,
                                key['id'],
                                None,
                                None,
                                None,
                                value,
                                None,
                            )
                        elif len(value) < 2712 :
                             yield (
                                document.id,
                                key['id'],
                                None,
                                None,
                                None,
                                None,
                                value,
                            )
                        else :
                            print("La taille de la ligne index,   \
                            dépasse le maximum, 2712, pour l'index \
                            « ix_nodes_hyperdata_value_txt » HINT:  \
                            Les valeurs plus larges qu'un tiers d'une\
                            page de tampon ne peuvent pas être        \
                            indexées (sur postgres 9.5). TODO :        \
                            Utilisez un index sur le hachage MD5 de la  \
                            valeur et/ou passez à l'indexation de la     \
                            recherche plein texte.")

                            yield (
                                document.id,
                                key['id'],
                                None,
                                None,
                                None,
                                None,
                                value[:2712],
                            )




                    else:
                        print("WARNING: Couldn't insert an INDEXED_HYPERDATA value because of unknown type:", type(value))


def index_hyperdata(corpus):
    bulk_insert(
        table = NodeHyperdata,
        fields = ( 'node_id', 'key'
                 , 'value_int'
                 , 'value_flt'
                 , 'value_utc'
                 , 'value_str'
                 , 'value_txt' ),
        data = _nodes_hyperdata_generator(corpus),
    )
