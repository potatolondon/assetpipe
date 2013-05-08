
from collections import OrderedDict
import os
import StringIO
from django.conf import settings
from django.utils.encoding import smart_str
from ..base import Processor
from django.core.exceptions import ImproperlyConfigured

class ClosureCompiler(Processor):

    def modify_expected_output_filenames(self, filenames):
        return filenames

    def process(self, inputs):
        if not hasattr(settings, "CLOSURE_COMPILER_BINARY"):
            raise ImproperlyConfigured("Please set the CLOSURE_COMPILER_BINARY setting")

        from subprocess import Popen, PIPE

        outputs = OrderedDict()

        compressor = settings.CLOSURE_COMPILER_BINARY
        try:
            for filename, contents in inputs.items():
                cmd = Popen([
                    'java', '-jar', compressor],
                    stdin=PIPE, stdout=PIPE, stderr=PIPE,
                    universal_newlines=True
                )
                output, error = cmd.communicate(smart_str(contents.read()))

                file_out = StringIO.StringIO()
                file_out.write(output)
                file_out.seek(0)
                outputs[filename] = file_out

        except Exception, e:
            raise ValueError("Failed to execute Java VM or closure. "
                    "Please make sure that you have installed Java "
                    "and that it's in your PATH and that you've configured "
                    "CLOSURE_COMPILER_BINARY in your settings correctly.\n"
                    "Error was: %s" % e)

        return outputs
