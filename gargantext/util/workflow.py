from gargantext.util.db import *
from gargantext.models import *
from gargantext.util.scheduling import scheduled

from gargantext.constants import *


@scheduled
def parse(corpus_id):
    # retrieve corpus from database
    corpus = session.query(Node).filter(Node.id == corpus_id).first()
    if corpus is None:
        print('NO SUCH CORPUS: #%d' % corpus_id)
        return
    # retrieve resource information
    documents_count = 0
    for resource in corpus['resources']:
        # information about the resource
        resource_parser = RESOURCETYPES[resource['type']]['parser']
        resource_path = resource['path']
        # extract and insert documents from corpus resource into database
        for hyperdata in resource_parser(resource_path):
            document = corpus.add_child(
                typename = 'DOCUMENT',
                name = hyperdata.get('title', '')[:255],
                hyperdata = hyperdata,
            )
            session.add(document)
            if documents_count % 64 == 0:
                corpus.status(action='parsing', progress=documents_count, autocommit=True)
            documents_count += 1
    # commit all changes
    corpus.status(action='parsing', progress=documents_count)
    session.commit()
