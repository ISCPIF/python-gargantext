from django.core.management.base import BaseCommand, CommandError
from gargantext.models import Node


class Command(BaseCommand):
    help = 'Something'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Oh yeah!'))
