from collections import OrderedDict
import ntpath
import StringIO

from ..base import Processor


class Prepend(Processor):
    def __init__(self, pipeline, additional_files):
        super(Prepend, self).__init__(pipeline)
        self.additional_files = additional_files

    def process(self, inputs):
        """
            Concatenates the inputs into a single file
        """
        output = StringIO.StringIO()
        for f in self.additional_files:
            output.write(open(f).read())
            output.write("\n")

        for contents in inputs.values():
            output.write(contents.read())
            output.write("\n")

        output.seek(0) #Rewind to the beginning

        return OrderedDict([(ntpath.basename(f), output)])

    def prepare(self, inputs):
        result = []
        for f in self.additional_files:
            result.append((f, None))

        for k, v in inputs.items():
            result.append((k, v))

        return OrderedDict(result)
