from django.core.management.base import BaseCommand, CommandError
from gargantext.util.show_nodes import tree_show, nodes
import colorama


class Command(BaseCommand):
    help = 'Nodes'

    def add_arguments(self, parser):
        parser.add_argument(dest='action', default='show')

    def handle(self, *args, **options):
        action = options.get('action')

        if action == 'show':
            colorama.init(strip=False)
            for root in nodes():
                tree_show(root)
