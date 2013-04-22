import sys

from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    """ Command for generating production assets."""

    help = 'Generate production assets.'
    extra_options = []
    option_list = BaseCommand.option_list + tuple(extra_options)

    def handle(self, *args, **options):
        self.stdout = getattr(self, 'stdout', sys.stdout)

        settings.on_production_server = True

        for pipeline in settings.ASSET_PIPELINES["LIVE"]:
            self.stdout.write("Running pipeline.\n")
            pipeline.run()

