
from collections import OrderedDict
import os
import StringIO
from django.conf import settings
from django.utils.encoding import smart_str
from ..base import Minifier

class YUI(Minifier):
    def minify(self, inputs):
        from subprocess import Popen, PIPE

        outputs = OrderedDict()

        compressor = settings.YUI_COMPRESSOR_BINARY
        try:
            for filename, contents in inputs.items():
                filetype = os.path.splitext(filename)[-1].lstrip(".")
                cmd = Popen([
                    'java', '-jar', compressor,
                    '--charset', 'utf-8', '--type', filetype],
                    stdin=PIPE, stdout=PIPE, stderr=PIPE,
                    universal_newlines=True
                )
                output, error = cmd.communicate(smart_str(contents.read()))

                file_out = StringIO.StringIO()
                file_out.write(output)
                file_out.seek(0)
                outputs[filename] = file_out

        except Exception, e:
            raise ValueError("Failed to execute Java VM or yuicompressor. "
                    "Please make sure that you have installed Java "
                    "and that it's in your PATH and that you've configured "
                    "YUICOMPRESSOR_PATH in your settings correctly.\n"
                    "Error was: %s" % e)

        return outputs
