from collections import defaultdict
from datetime import datetime
from random import random
from hashlib import md5
from time import time
from math import log

from gargantext_web.db import *

from .FileParsers import *



class DebugTime:

    def __init__(self, prefix):
        self.prefix = prefix
        self.message = None
        self.time = None

    def __del__(self):
        if self.message is not None and self.time is not None:
            print('%s - %s: %.4f' % (self.prefix, self.message, time() - self.time))

    def show(self, message):
        self.__del__()
        self.message = message
        self.time = time()


# keep all the parsers in a cache
class Parsers(defaultdict):

    _parsers = {
        'pubmed'            : PubmedFileParser,
        'isi'               : IsiFileParser,
        'ris'               : RisFileParser,
        'europress'         : EuropressFileParser,
        'europress_french'  : EuropressFileParser,
        'europress_english' : EuropressFileParser,
    }

    def __missing__(self, key):
        if key not in self._parsers:
            raise NotImplementedError('No such parser: "%s"' % (key))
        parser = self._parsers[key]()
        self[key] = parser
        return parser

parsers = Parsers()



# resources managment

def add_resource(corpus, **kwargs):
    # only for tests
    session = Session()
    resource = Resource(guid=str(random()), **kwargs )
    # User
    if 'user_id' not in kwargs:
        resource.user_id = corpus.user_id
    # Compute the digest
    h = md5()
    f = open(str(resource.file), 'rb')
    h.update(f.read())
    f.close()
    resource.digest = h.hexdigest()
    # check if a resource on this node already has this hash
    tmp_resource = (session
        .query(Resource)
        .join(Node_Resource, Node_Resource.resource_id == Resource.id)
        .filter(Resource.digest == resource.digest)
        .filter(Node_Resource.node_id == corpus.id)
    ).first()
    if tmp_resource is not None:
        return tmp_resource
    else:
        session.add(resource)
        session.commit()
    # link with the resource
    node_resource = Node_Resource(
        node_id = corpus.id,
        resource_id = resource.id,
        parsed = False,
    )
    session.add(node_resource)
    session.commit()
    # return result
    return resource


def parse_resources(corpus, user=None, user_id=None):
    dbg = DebugTime('Corpus #%d - parsing' % corpus.id)
    session = Session()
    corpus_id = corpus.id
    type_id = cache.NodeType['Document'].id
    if user_id is None and user is not None:
        user_id = user.id
    else:
        user_id = corpus.user_id
    # find resource of the corpus
    resources_query = (session
        .query(Resource, ResourceType)
        .join(ResourceType, ResourceType.id == Resource.type_id)
        .join(Node_Resource, Node_Resource.resource_id == Resource.id)
        .filter(Node_Resource.node_id == corpus.id)
        .filter(Node_Resource.parsed == False)
    )
    # make a new node for every parsed document of the corpus
    dbg.show('analyze documents')
    nodes = list()
    for resource, resourcetype in resources_query:
        parser = parsers[resourcetype.name]
        for metadata_dict in parser.parse(resource.file):
            # retrieve language ID from metadata
            if 'language_iso2' in metadata_dict:
                try:
                    language_id = cache.Language[metadata_dict['language_iso2']].id
                except KeyError:
                    language_id = None
            else:
                language_id = None
            # create new node
            node = Node(
                name = metadata_dict.get('title', '')[:200],
                parent_id = corpus_id,
                user_id = user_id,
                type_id = type_id,
                language_id = language_id,
                metadata = metadata_dict,
                date = datetime.utcnow(),
            )
            nodes.append(node)
            #
            # TODO: mark node-resources associations as parsed
            # 
    dbg.show('insert %d documents' % len(nodes))
    session.add_all(nodes)
    session.commit()
    # now, index the metadata
    dbg.show('insert metadata')
    node_metadata_lists = defaultdict(list)
    metadata_types = {
        metadata.name: metadata
        for metadata in session.query(Metadata)
    }
    for node in nodes:
        node_id = node.id
        for metadata_key, metadata_value in node.metadata.items():
            try:
                metadata = metadata_types[metadata_key]
            except KeyError:
                continue
            if metadata.type == 'string':
                metadata_value = metadata_value[:255]
            node_metadata_lists[metadata.type].append((
                node_id,
                metadata.id,
                metadata_value,
            ))
    for key, values in node_metadata_lists.items():
        bulk_insert(Node_Metadata, ['node_id', 'metadata_id', 'value_'+key], values)
    # mark the corpus as parsed
    corpus.parsed = True


# ngrams extraction

from .NgramsExtractors import EnglishNgramsExtractor, FrenchNgramsExtractor, NgramsExtractor

class NgramsExtractors(defaultdict):

    def __init__(self):
        # English
        self['en'] = EnglishNgramsExtractor()
        for key in ('eng', 'english'):
            self[key] = self['en']
        # French
        self['fr'] = FrenchNgramsExtractor()
        for key in ('fre', 'french'):
            self[key] = self['fr']
        # default
        self['default'] = NgramsExtractor()

    def __missing__(self, key):
        formatted_key = key.strip().lower()
        if formatted_key in self:
            self[key] = self[formatted_key]
        else:
            self[key] = self['default']
            # raise NotImplementedError
        return self[key]

ngramsextractors = NgramsExtractors()

def extract_ngrams(corpus, keys):
    print("yoloo")
    dbg = DebugTime('Corpus #%d - ngrams' % corpus.id)
    default_language_iso2 = None if corpus.language_id is None else cache.Language[corpus.language_id].iso2
    # query the metadata associated with the given keys
    columns = [Node.id, Node.language_id] + [Node.metadata[key] for key in keys]
    metadata_query = (session
        .query(*columns)
        .filter(Node.parent_id == corpus.id)
        .filter(Node.type_id == cache.NodeType['Document'].id)
    )
    # prepare data to be inserted
    dbg.show('find ngrams')
    languages_by_id = {
        language.id: language.iso2
        for language in session.query(Language)
    }
    ngrams_data = set()
    node_ngram_list = defaultdict(lambda: defaultdict(int))
    for nodeinfo in metadata_query:
        node_id = nodeinfo[0]
        language_id = nodeinfo[1]
        if language_id is None:
            language_iso2 = default_language_iso2
        else:
            language_iso2 = languages_by_id.get(language_id, None)
        if language_iso2 is None:
            continue
        ngramsextractor = ngramsextractors[language_iso2]
        for text in nodeinfo[2:]:
            if text is not None and len(text):
                ngrams = ngramsextractor.extract_ngrams(text.replace("[","").replace("]",""))
                for ngram in ngrams:
                    terms = ' '.join([token for token, tag in ngram]).lower()
                    n = len(ngram)
                    node_ngram_list[node_id][terms] += 1
                    ngrams_data.add(
                        (n, terms)
                    )
    # insert ngrams to temporary table
    dbg.show('find ids for the %d ngrams' % len(ngrams_data))
    db, cursor = get_cursor()
    cursor.execute('''
        CREATE TEMPORARY TABLE tmp__ngrams (
            id INT,
            n INT NOT NULL,
            terms VARCHAR(255) NOT NULL
        )
    ''')
    bulk_insert('tmp__ngrams', ['n', 'terms'], ngrams_data, cursor=cursor)
    # retrieve ngram ids from already inserted stuff
    cursor.execute('''
        UPDATE
            tmp__ngrams
        SET
            id = ngram.id
        FROM
            %s AS ngram
        WHERE
            ngram.terms = tmp__ngrams.terms
    ''' % (Ngram.__table__.name, ))
    # insert, then get the ids back
    cursor.execute('''
        INSERT INTO
            %s (n, terms)
        SELECT
            n, terms
        FROM
            tmp__ngrams
        WHERE
            id IS NULL
    ''' % (Ngram.__table__.name, ))
    cursor.execute('''
        UPDATE
            tmp__ngrams
        SET
            id = ngram.id
        FROM
            %s AS ngram
        WHERE
            ngram.terms = tmp__ngrams.terms
        AND
            tmp__ngrams.id IS NULL
    ''' % (Ngram.__table__.name, ))
    # get all ids
    ngram_ids = dict()
    cursor.execute('SELECT id, terms FROM tmp__ngrams')
    for row in cursor.fetchall():
        ngram_ids[row[1]] = row[0]
    # 
    dbg.show('insert associations')
    node_ngram_data = list()
    for node_id, ngrams in node_ngram_list.items():
        for terms, weight in ngrams.items():
            try:
                ngram_id = ngram_ids[terms]
                node_ngram_data.append((node_id, ngram_id, weight, ))
            except Exception as e:
                print("err01:",e)
    bulk_insert(Node_Ngram, ['node_id', 'ngram_id', 'weight'], node_ngram_data, cursor=cursor)
    dbg.message = 'insert %d associations' % len(node_ngram_data)
    # commit to database
    db.commit()



# tfidf calculation

def compute_tfidf(corpus):
    dbg = DebugTime('Corpus #%d - tfidf' % corpus.id)
    # compute terms frequency sum
    dbg.show('calculate terms frequencies sums')
    db, cursor = get_cursor()
    cursor.execute('''
        CREATE TEMPORARY TABLE tmp__st (
            node_id INT NOT NULL,
            frequency DOUBLE PRECISION NOT NULL
        )
    ''')
    cursor.execute('''
        INSERT INTO
            tmp__st (node_id, frequency)
        SELECT
            node_ngram.node_id,
            SUM(node_ngram.weight) AS frequency
        FROM
            %s AS node
        INNER JOIN
            %s AS node_ngram ON node_ngram.node_id = node.id
        WHERE
            node.parent_id = %d
        GROUP BY
            node_ngram.node_id
    ''' % (Node.__table__.name, Node_Ngram.__table__.name, corpus.id, ))
    # compute normalized terms frequencies
    dbg.show('normalize terms frequencies')
    cursor.execute('''
        CREATE TEMPORARY TABLE tmp__tf (
            node_id INT NOT NULL,
            ngram_id INT NOT NULL,
            frequency DOUBLE PRECISION NOT NULL
        )
    ''')
    cursor.execute('''
        INSERT INTO
            tmp__tf (node_id, ngram_id, frequency)
        SELECT
            node_ngram.node_id,
            node_ngram.ngram_id,
            (node_ngram.weight / node.frequency) AS frequency
        FROM
            %s AS node_ngram
        INNER JOIN
            tmp__st AS node ON node.node_id = node_ngram.node_id
    ''' % (Node_Ngram.__table__.name, ))
    # show off
    dbg.show('compute idf')
    cursor.execute('''
        CREATE TEMPORARY TABLE tmp__idf (
            ngram_id INT NOT NULL,
            idf DOUBLE PRECISION NOT NULL
        )
    ''')
    cursor.execute('''
        INSERT INTO
            tmp__idf(ngram_id, idf)
        SELECT
            node_ngram.ngram_id,
            -ln(COUNT(*))
        FROM
            %s AS node
        INNER JOIN
            %s AS node_ngram ON node_ngram.node_id = node.id
        WHERE
            node.parent_id = %d
        GROUP BY
            node_ngram.ngram_id
    ''' % (Node.__table__.name, Node_Ngram.__table__.name, corpus.id, ))
    cursor.execute('SELECT COUNT(*) FROM tmp__st')
    D = cursor.fetchone()[0]
    if D>0:
        lnD = log(D)
        cursor.execute('UPDATE tmp__idf SET idf = idf + %f' % (lnD, ))
        # show off
        dbg.show('insert tfidf for %d documents' % D)
        cursor.execute('''
            INSERT INTO
                %s (nodex_id, nodey_id, ngram_id, score)
            SELECT
                %d AS nodex_id,
                tf.node_id AS nodey_id,
                tf.ngram_id AS ngram_id,
                (tf.frequency * idf.idf) AS score
            FROM
                tmp__idf AS idf
            INNER JOIN
                tmp__tf AS tf ON tf.ngram_id = idf.ngram_id
        ''' % (NodeNodeNgram.__table__.name, corpus.id, ))
        # # show off
        # cursor.execute('''
        #     SELECT
        #         node.name,
        #         ngram.terms,
        #         node_node_ngram.score AS tfidf
        #     FROM
        #         %s AS node_node_ngram
        #     INNER JOIN
        #         %s AS node ON node.id = node_node_ngram.nodey_id
        #     INNER JOIN
        #         %s AS ngram ON ngram.id = node_node_ngram.ngram_id
        #     WHERE
        #         node_node_ngram.nodex_id = %d
        #     ORDER BY
        #         score DESC
        # ''' % (NodeNodeNgram.__table__.name, Node.__table__.name, Ngram.__table__.name, corpus.id, ))
        # for row in cursor.fetchall():
        #     print(row)
        # the end!
        db.commit()
