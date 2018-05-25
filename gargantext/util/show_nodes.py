# Make this a standalone script...
# Can be called this way: python3 gargantext/util/show_nodes.py

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gargantext.settings')
django.setup()

# ...End of jiberish.

import itertools
import colorama
from colorama import Fore
from sqlalchemy.sql.expression import literal_column

from gargantext.util.db import session, func, aliased
from gargantext.models import Node


NODE_BULLET = '‣'

# https://en.wikipedia.org/wiki/Box-drawing_character
TREE_ROOT = '╾'
TREE_VERT = '│'
TREE_HORI = '─'
TREE_FORK = '├'
TREE_CORN = '└'

FIRST  = 0x01
LAST   = 0x02


def nodes(parent=None, group_by='typename', order_by='typename', has_child='check'):
    if group_by or has_child is not None:
        select = [func.min(Node.id).label('id'),
                  func.min(Node.name).label('name'),
                  func.min(Node.typename).label('typename'),
                  func.count(Node.id).label('cnt')]
    else:
        select = [Node.id.label('id'),
                  Node.name.label('name'),
                  Node.typename.label('typename'),
                  literal_column('1').label('cnt')]

    if has_child is not None:
        N = aliased(Node)
        select.append(func.count(N.id).label('children'))
    else:
        select.append(literal_column('NULL').label('children'))

    parent_id = getattr(parent, 'id', parent)
    q = session.query(*select).filter_by(parent_id=parent_id) \
               .group_by(getattr(Node, group_by if group_by else 'id'))

    if has_child is not None:
        q = q.outerjoin(N, N.parent_id == Node.id).group_by(N.parent_id)

    return q.order_by(order_by)


def node_show(node, prefix='', maxlen=60):
    if node.children > 0 or node.cnt == 1:
        node_id = '<{}> '.format(node.id)
        name = node.name[:maxlen] + '..' if len(node.name) > maxlen else node.name
        label = node_id + Fore.CYAN + name + Fore.RESET
    else:
        label = Fore.MAGENTA + str(node.cnt) + Fore.RESET

    typename = Fore.GREEN + node.typename + Fore.RESET
    print(prefix, '%s %s' % (typename, label), sep='')


def tree_show(node, pos=FIRST|LAST, level=0, prefix='', maxlen=60, compact=True):
    #print('%02d %x' % (level, pos), end='')

    branch = TREE_ROOT if pos&FIRST and level == 0 else TREE_FORK if not pos&LAST else TREE_CORN
    node_prefix = prefix + branch + 2*TREE_HORI + ' '
    node_show(node, node_prefix, maxlen)

    childs = iter(nodes(parent=node, group_by=compact and 'typename'))

    try:
        node = next(childs)
    except StopIteration:
        return

    prefix = prefix + (' ' if pos&LAST else TREE_VERT) + '   '

    for i, next_node in enumerate(itertools.chain(childs, [None])):
        pos = (FIRST if i == 0 else 0) | (LAST if next_node is None else 0)
        tree_show(node, pos, level + 1, prefix, maxlen, compact)
        node = next_node


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        compact = True
    elif len(sys.argv) == 2 and sys.argv[1] in ('-a', '--all'):
        compact = False
    else:
        print("Usage: %s [-a|--all]" % sys.argv[0], file=sys.stderr)
        sys.exit(1)

    colorama.init(strip=False)
    for root in nodes():
        tree_show(root, compact=compact)
