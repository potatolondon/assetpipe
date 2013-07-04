from collections import OrderedDict
from ..base import Processor
import StringIO

class Prepend(Processor):
    def __init__(self, pipeline, additional_files):
        super(Prepend, self).__init__(pipeline)
        self.additional_files = additional_files

    def process(self, inputs):
        """
            Concatenates the inputs into a single file
        """

        result = []
        for f in self.additional_files:
            s = StringIO.StringIO()
            s.write(open(f).read())
            s.seek(0)
            result.append((f, s))

        for k, v in inputs.items():
            result.append((k, v))

        return OrderedDict(result)

    def prepare(self, inputs):
        result = []
        for f in self.additional_files:
            result.append((f, None))

        for k, v in inputs.items():
            result.append((k, v))

        return OrderedDict(result)
