""" Base classes for the processors and outputters.
    You can extend these to make your own processors and outputters.
"""
import os

class Processor(object):

    def __init__(self, pipeline):
        """ The pipeline is passed in so that you can access it if you need to.
            The args and kwargs that you pass into .Process() when defining your
            pipeline are also passed in here.
        """
        self.pipeline = pipeline

    def modify_expected_output_filenames(self, filenames):
        """ Given the existing list of filenames, return the list of
            filenames as it will be after self.processs() has run.
        """
        raise NotImplementedError()

    def process(self, inputs):
        """ Given the inputs (an OrderedDict of filename: StringIO(output) mappings),
            modify them however you like (e.g. minify or concatenate them) and return
            the processed output files in the same OrderedDict format.
        """
        raise NotImplementedError()


class Outputter(object):
    def __init__(self, directory=None):
        self.directory = directory

    def output(self, filename, file_out):
        raise NotImplementedError()


class NullOutputter(object):
    def __init__(self, directory):
        self.cache = set()

    def output(self, filename, file_out):
        self.cache.add(filename)

    def file_up_to_date(self, filename):
        return filename in self.cache


def read_generated_media_file(active_pipeline=None):
    from django.conf import settings
    from django.utils import simplejson

    filename = settings.ASSET_MEDIA_URLS_FILE
    active_pipeline = active_pipeline or settings.ASSET_PIPELINE_ACTIVE

    #Make the filename active pipeline specific
    path, ext = os.path.splitext(filename)
    filename = ".".join([path, active_pipeline.lower(), ext.lstrip(".")])
    return simplejson.loads(open(filename).read())

def build_generated_media_file(active_pipeline=None):
    from django.conf import settings
    from django.utils import simplejson

    filename = settings.ASSET_MEDIA_URLS_FILE
    active_pipeline = active_pipeline or settings.ASSET_PIPELINE_ACTIVE

    #Make the filename active pipeline specific
    path, ext = os.path.splitext(filename)
    filename = ".".join([path, active_pipeline.lower(), ext.lstrip(".")])

    final = {}
    for k, v in settings.ASSET_PIPELINES[active_pipeline].items():
        final[k] = v.output_urls()

    with open(filename, "w") as f:
        f.write(simplejson.dumps(final))
