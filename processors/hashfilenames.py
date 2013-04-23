from collections import OrderedDict
import os
from ..base import Processor


class HashFileNames(Processor):

    def modify_expected_output_filenames(self, filenames):
        modified = []
        for filename in filenames:
            modified.append(self._add_hash_to_filename(filename))
        return modified

    def process(self, inputs):
        outputs = OrderedDict()
        for filename, contents in inputs.items():
            filename = self._add_hash_to_filename(filename)
            outputs[filename] = contents
        return outputs

    def _add_hash_to_filename(self, filename):
        hsh = self.pipeline._root().pipeline_hash
        part, ext = os.path.splitext(filename)
        return ".".join([part, hsh, ext.lstrip(".")])
