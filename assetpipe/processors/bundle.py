from collections import OrderedDict
import StringIO
from ..base import Processor


class Bundle(Processor):
    def __init__(self, pipline, output_file_name):
        super(Bundle, self).__init__(pipline)
        self.output_file_name = output_file_name

    def process(self, inputs):
        """
            Concatenates the inputs into a single file
        """
        output = StringIO.StringIO()
        for contents in inputs.values():
            output.write(contents.read())
            output.write("\n")
        output.seek(0) #Rewind to the beginning
        return OrderedDict([(self.output_file_name, output)])

    def prepare(self, inputs):
        return OrderedDict([(self.output_file_name, None)])
