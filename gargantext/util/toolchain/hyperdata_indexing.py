from gargantext.util.db import bulk_insert
from gargantext.constants import INDEXED_HYPERDATA
from gargantext.models import NodeHyperdata


def _nodes_hyperdata_generator(corpus):
    """This method generates columns for insertions in `nodes_hyperdata`.
    In case one of the values is a list, its items are iterated over and
    yielded separately.
    """
    for document in corpus.children(typename='DOCUMENT'):
        for keyname, key in INDEXED_HYPERDATA.items():
            if keyname in document.hyperdata:
                values = key['convert_to_db'](document.hyperdata[keyname])
                if not isinstance(values, list):
                    values = [values]
                for value in values:
                    if isinstance(value, (int, float, )):
                        yield (
                            document.id,
                            key['id'],
                            value,
                            None,
                        )
                    elif isinstance(value, (str, )):
                        yield (
                            document.id,
                            key['id'],
                            None,
                            value[:255],
                        )


def index_hyperdata(corpus):
    bulk_insert(
        table = NodeHyperdata,
        fields = ('node_id', 'key', 'value_flt', 'value_str', ),
        data = _nodes_hyperdata_generator(corpus),
    )
