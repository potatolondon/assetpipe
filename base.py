""" Base classes for the processors and outputters.
    You can extend these to make your own processors and outputters.
"""


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

