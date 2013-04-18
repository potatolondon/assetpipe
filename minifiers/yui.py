
import StringIO
from django.conf import settings
from django.utils.encoding import smart_str
from ..base import Minifier

class YUI(Minifier):
    def minify(self, filetypes, inputs):
        from subprocess import Popen, PIPE

        results = []

        compressor = settings.YUI_COMPRESSOR_BINARY
        try:
            for i, inp in enumerate(inputs):
                cmd = Popen([
                    'java', '-jar', compressor,
                    '--charset', 'utf-8', '--type', filetypes[i]],
                    stdin=PIPE, stdout=PIPE, stderr=PIPE,
                    universal_newlines=True
                )
                output, error = cmd.communicate(smart_str(inp.read()))

                file_out = StringIO.StringIO()
                file_out.write(output)
                file_out.seek(0)
                results.append(file_out)

        except Exception, e:
            raise ValueError("Failed to execute Java VM or yuicompressor. "
                    "Please make sure that you have installed Java "
                    "and that it's in your PATH and that you've configured "
                    "YUICOMPRESSOR_PATH in your settings correctly.\n"
                    "Error was: %s" % e)

        return results
