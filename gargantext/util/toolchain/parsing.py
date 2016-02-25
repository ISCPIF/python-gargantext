from gargantext.util.db import *
from gargantext.models import *
from gargantext.constants import *


def parse(corpus):
    try:
        documents_count = 0
        corpus.status('parsing', progress=0)
        # retrieve resource information
        for resource in corpus.resources():
            # information about the resource
            if resource['extracted']:
                continue
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
                if documents_count % BATCH_PARSING_SIZE == 0:
                    corpus.status('parsing', progress=documents_count)
                    corpus.save_hyperdata()
                    session.commit()
                documents_count += 1
            # update info about the resource
            resource['extracted'] = True
        # commit all changes
        corpus.status('parsing', progress=documents_count, complete=True)
        corpus.save_hyperdata()
        session.commit()
    except Exception as error:
        corpus.status('parsing', error=error)
        corpus.save_hyperdata()
        session.commit()
        raise error
