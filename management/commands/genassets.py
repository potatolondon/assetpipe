import sys
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from assetpipe.base import build_generated_media_file

class Command(BaseCommand):
    """ Command for generating production assets."""

    help = 'Generate production assets.'
    extra_options = [
        make_option('--pipeline', action='store', dest='pipeline',
            help='Specified which pipeline to run'
        ),
    ]
    option_list = BaseCommand.option_list + tuple(extra_options)

    def handle(self, *args, **options):
        self.stdout = getattr(self, 'stdout', sys.stdout)

        if not options.get("pipeline"):
            raise CommandError("You must specify a pipeline to run")

        if options["pipeline"] not in settings.ASSET_PIPELINES:
            raise CommandError("%s is not a valid pipline" % options["pipeline"])

        for k, v in settings.ASSET_PIPELINES[options["pipeline"]].items():
            v.run()

        build_generated_media_file(options["pipeline"])

