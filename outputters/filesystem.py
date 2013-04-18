import os
from hashlib import md5
from ..base import Outputter

class Filesystem(Outputter):
    def output(self, filename, file_out):
        content = file_out.read()
        hsh = md5(content).hex_digest()
        filename, ext = os.path.splitext(filename)
        out_filename = os.path.join(self.directory, filename + "." + hsh + "." + ext)
        open(out_filename, "w").write(content)
        return out_filename



