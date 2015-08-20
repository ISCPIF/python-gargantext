from gargantext_web.db import models, bulk_insert, Session, get_cursor, engine, Base


from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.schema import Column, ForeignKey, Index
from sqlalchemy.types import *
from sqlalchemy.orm import relationship, aliased

from collections import deque, defaultdict
import re
_re_sentence = re.compile(r'''(?:["']?[A-Z][^.?!]+|^)(?:(?![.?!]['"]?\s["']?[A-Z][^.?!]).)+(?:[.?!'"]+|$)''', re.UNICODE | re.MULTILINE | re.DOTALL)

from parsing.NgramsExtractors.TurboNgramsExtractor import TurboNgramsExtractor
ngramsextractor = TurboNgramsExtractor()

from sqlalchemy.sql import func


class Node(Base):
    __tablename__ = models.Node._meta.db_table
    id = Column(Integer, primary_key=True, nullable=False)
    # data type
    nodetype = Column(String(1), nullable=False, default=' ')
    # hierarchy
    user_id = Column(Integer, ForeignKey('%s.id' % models.User._meta.db_table, ondelete='CASCADE'), index=False)
    # nestedness
    lft = Column(Integer, nullable=False, default=0)
    rgt = Column(Integer, nullable=False, default=1)
    depth = Column(Integer, nullable=False, default=0)
    # values
    name = Column(String(255), nullable=False)
    contents = Column(Text)

    # default constructor
    def __init__(self, *args, **kwargs):
        self.parent = None
        self.children = deque()
        super(self.__class__, self).__init__(*args, **kwargs)

    # string representation
    def __repr__(self):
        return '<%s id=%s, type=%s, lft=%s, rgt=%s, depth=%s, name=%s, contents=%s>' % (
            self.__class__.__name__,
            self.id,
            repr(self.nodetype),
            self.lft,
            self.rgt,
            self.depth,
            repr(self.name if self.name is not None else None),
            (repr(self.contents[:64]) + ('...' if len(self.contents) > 64 else '')) if self.contents is not None else None,
        )

    def __str__(self):
        result = (self.depth if self.depth else 0) * '    ' + repr(self)
        if hasattr(self, 'children'):
            for child in self.children:
                result += '\n'
                result += str(child)
        return result

    # get children for the selected node
    def fetch_descendants(self):
        session = Session()
        nodes = (session
            .query(Node)
            .filter(Node.user_id == self.user_id)
            .filter(Node.lft > self.lft)
            .filter(Node.lft < self.rgt)
            .order_by(Node.lft)
        )
        self.children = deque()
        depth2node = {0: self}
        for node in nodes:
            node.children = deque()
            depth2node[node.depth] = node
            depth2node[node.depth - 1].children.append(node)
    def fetch_descendants_ngrams(self):
        from gargantext_web.db import NodeNgram, Ngram
        session = Session()
        ngrams = (session
            .query(Ngram.terms, func.sum(NodeNgram.weight))
            .join(NodeNgram, NodeNgram.ngram_id == Ngram.id)
            .join(Node, Node.id == NodeNgram.node_id)
            .filter(Node.user_id == self.user_id)
            .filter(Node.lft >= self.lft)
            .filter(Node.lft <= self.rgt)
            .group_by(Ngram.terms)
            .order_by(func.sum(NodeNgram.weight).desc())
        )
        return ngrams 

    # hierarchical operations between nodes
    def insert_before(self, sibling):
        pass
    def insert_after(self, sibling):
        pass
    def prepend(self, child):
        self.children.appendleft(child)
        if self.id is not None:
            db, cursor = get_cursor()
            # parent node's characteristics
            cursor.execute('SELECT lft FROM ' + self.__tablename__ + ' WHERE id = %s', (self.id, ))
            node = cursor.fetchone()
            if node is not None:
                lft = node[0]
            else:
                raise ValueError('No node found for id = %s (tip: maybe committing to the database would help)')
            # what to do?
            inserted_nodes = []
            updated_nodes = []
            span = child.compute_nested(lft + 1, self.depth + 1, inserted_nodes, updated_nodes)
            # shift stuff to the right
            cursor.execute('UPDATE ' + self.__tablename__ + ' SET lft = lft + %s WHERE user_id = %s AND lft > %s', (span, self.user_id, lft, ))
            cursor.execute('UPDATE ' + self.__tablename__ + ' SET rgt = rgt + %s WHERE user_id = %s AND rgt > %s', (span, self.user_id, lft, ))
            self.rgt += span
            # insert nodes
            bulk_insert(
                self.__tablename__,
                ('nodetype', 'user_id', 'lft', 'rgt', 'depth', 'name', 'contents', ),
                ((node.nodetype, self.user_id, node.lft, node.rgt, node.depth, node.name, node.contents, ) for node in inserted_nodes),
                cursor,
            )
            # update nodes
            for node in updated_nodes:
                cursor.execute('UPDATE ' + self.__tablename__ + ' SET lft = %s, rgt = %s WHERE id = %s', (node.lft, node.rgt, node.id, ))
            # commit to database
            db.commit()
    def append(self, child, session=None):
        self.children.append(child)
        if self.id is not None:
            db, cursor = get_cursor()
            # parent node's characteristics
            cursor.execute('SELECT rgt FROM ' + self.__tablename__ + ' WHERE id = %s', (self.id, ))
            node = cursor.fetchone()
            if node is not None:
                rgt = node[0]
            else:
                raise ValueError('No node found for id = %s (tip: maybe committing to the database would help)')
            # what to do?
            inserted_nodes = []
            updated_nodes = []
            span = child.compute_nested(rgt, self.depth + 1, inserted_nodes, updated_nodes)
            # shift stuff to the right
            cursor.execute('UPDATE ' + self.__tablename__ + ' SET lft = lft + %s WHERE user_id = %s AND lft >= %s', (span, self.user_id, rgt, ))
            cursor.execute('UPDATE ' + self.__tablename__ + ' SET rgt = rgt + %s WHERE user_id = %s AND rgt >= %s', (span, self.user_id, rgt, ))
            self.rgt += span
            # insert nodes
            bulk_insert(
                self.__tablename__,
                ('nodetype', 'user_id', 'lft', 'rgt', 'depth', 'name', 'contents', ),
                ((node.nodetype, self.user_id, node.lft, node.rgt, node.depth, node.name, node.contents, ) for node in inserted_nodes),
                cursor,
            )
            # update nodes
            for node in updated_nodes:
                cursor.execute('UPDATE ' + self.__tablename__ + ' SET lft = %s, rgt = %s WHERE id = %s', (node.lft, node.rgt, node.id, ))
            # commit to database
            db.commit()

    # compute lft and rgt value
    def compute_nested(self, lft, depth, inserted_nodes, updated_nodes):
        # what to do with this record
        if self.id is None:
            inserted_nodes.append(self)
        else:
            updated_nodes.append(self)
        # value for lft bound
        if lft is None:
            if self.lft is None:
                self.lft = 1
            lft = self.lft
        else:
            self.lft = lft
        # value for depth
        if depth is not None:
            self.depth = depth
        elif self.depth is None:
            self.depth = 0
        # iterate over children
        depth = self.depth + 1
        span = 2
        lft += 1
        for (index, child) in enumerate(self.children):
            child.user_id = self.user_id
            if child.name is None:
                child.name = {
                    'C': 'Corpus',
                    'D': 'Document',
                    'S': 'Section',
                    'c': 'Chapter',
                    'p': 'Paragraph',
                    's': 'Sentence',
                }.get(child.nodetype, 'Node') + ' #%d' % (index + 1)
            child_span = child.compute_nested(lft, depth, inserted_nodes, updated_nodes)
            lft += child_span
            span += child_span
        # rgt bound
        self.rgt = self.lft + span - 1
        # space taken by the node and its children
        return span

    # extract ngrams for all children
    def extract_ngrams(self, *sections):
        # initiate connections
        session = Session()
        db, cursor = get_cursor()
        # which sections should we process?
        if len(sections) == 1 and not isinstance(sections[0], str):
            sections = sections[0]
        # process all sections...
        if len(sections) == 0:
            nodes_query = (session
                .query(Node.id, Node.contents)
                .filter(Node.user_id == self.user_id)
                .filter(Node.lft.between(self.lft, self.rgt))
            )
        # ...or only process said sections
        else:
            SectionNode = aliased(Node)
            nodes_query = (session
                .query(Node.id, Node.contents)
                .select_from(SectionNode)
                .filter(SectionNode.lft.between(self.lft, self.rgt))
                .filter(SectionNode.nodetype == 'S')
                .filter(SectionNode.name.in_(sections))
                .join(Node, Node.lft.between(SectionNode.lft, SectionNode.rgt))
            )
        # only take non-empty contents
        nodes_query = nodes_query.filter(Node.contents != None)
        # retrieve ngrams for each of the nodes
        ngram2node2count = defaultdict(lambda: defaultdict(int))
        node_id_list = list()
        for node_id, node_contents in nodes_query:
            node_id_list.append(node_id)
            ngrams = ngramsextractor.extract_ngrams(node_contents)
            for ngram_tuple in ngrams:
                ngram_terms = ' '.join(
                    (token[0] if token[1].startswith('NNP') else token[0].lower())
                    for token in ngram_tuple
                )
                ngram2node2count[ngram_terms][node_id] += 1;
        # remove node/ngram associations
        from gargantext_web.db import NodeNgram
        if node_id_list:
            cursor.execute('DELETE FROM ' + NodeNgram.__table__.name + ' WHERE node_id IN (' + ', '.join(map(str, node_id_list)) + ')')
        # retrieve ngram ids
        from gargantext_web.db import Ngram
        ngrams_query = (session
            .query(Ngram.id, Ngram.terms)
            .filter(Ngram.terms.in_(ngram2node2count.keys()))
        )
        ngram2id = {
            ngram_terms: ngram_id
            for ngram_id, ngram_terms in ngrams_query
        }
        # insert ngrams that haven't been found
        bulk_insert(
            Ngram,
            ('n', 'terms'),
            (   (ngram_terms.count(' ') + 1, ngram_terms)
                for ngram_terms in ngram2node2count
                if ngram_terms not in ngram2id
            ),
            cursor,
        )
        # this time, retrieve every ngram
        ngrams_terms_remaining = set(ngram2node2count.keys()) - set(ngram2id.keys())
        if ngrams_terms_remaining:
            ngrams_query = (session
                .query(Ngram.id, Ngram.terms)
                .filter(Ngram.terms.in_(ngrams_terms_remaining))
            )
            for ngram_id, ngram_terms in ngrams_query:
                ngram2id[ngram_terms] = ngram_id
        # insert ngram/node associations
        bulk_insert(
            NodeNgram,
            ('node_id', 'ngram_id', 'weight'),
            (   (node_id, ngram2id[ngram_terms], count)
                for ngram_terms, node2count in ngram2node2count.items()
                for node_id, count in node2count.items()
            ),
            cursor,
        )
        # commit to database
        db.commit()


    # parse various elements
    def parse(self, contents=None):
        if contents is None:
            contents = self.contents
            self.contents = None
        nodetypes = {
            'D': self.parse_document,
            'c': self.parse_chapter,
            'p': self.parse_paragraph,
            's': self.parse_sentence,
        }
        if self.nodetype in nodetypes:
            nodetypes[self.nodetype](contents)
            if self.nodetype != 's':
                self.contents = None

    def parse_document(self, contents):
        for section_name, section_contents in contents.items():
            section_node = self.__class__(nodetype='S', name=section_name)
            self.append(section_node)
            section_node.parse_section(section_contents)

    def parse_section(self, contents):
        for chapter_contents in contents.split('\f'):
            chapter_contents = chapter_contents.strip()
            if len(chapter_contents) == 0:
                continue
            chapter_node = self.__class__(nodetype='c')
            self.append(chapter_node)
            chapter_node.parse_chapter(chapter_contents)

    def parse_chapter(self, contents):
        for paragraph_contents in contents.split('\n\n'):
            paragraph_contents = paragraph_contents.strip()
            if len(paragraph_contents) == 0:
                continue
            paragraph_node = self.__class__(nodetype='p')
            self.append(paragraph_node)
            paragraph_node.parse_paragraph(paragraph_contents)

    def parse_paragraph(self, contents):
        for sentence_contents in _re_sentence.findall(contents):
            sentence_node = self.__class__(nodetype='s')
            self.append(sentence_node)
            sentence_node.parse(sentence_contents)

    def parse_sentence(self, contents):
        self.contents = contents

Index('IX__nodes__user_id__lft__nodetype', Node.user_id, Node.lft, Node.nodetype)
Index('IX__nodes__user_id__rgt', Node.user_id, Node.rgt)

# Base.metadata.tables['node_node'].create(bind = engine)
