from collections import OrderedDict
import os
import StringIO
from django.conf import settings
from ..base import Processor

class Closure(Processor):
    def __init__(self, pipline, js_dirs):
        super(Closure, self).__init__(pipline)
        self.js_dirs = js_dirs


    def modify_expected_output_filenames(self, filenames):
        #TODO: modify these here
        return filenames

    def process(self, inputs):
        assert(inputs)
        assert(self.js_dirs)

        from subprocess import Popen, PIPE

        outputs = OrderedDict()

        builder = settings.CLOSURE_BUILDER_BINARY
        try:
            command = ['python', builder, "--output_mode", "script" ]

            closure_dir = os.path.dirname(os.path.dirname(os.path.dirname(builder)))
            closure_deps = "%s/goog/deps.js" % closure_dir
            assert(os.path.exists(closure_deps))

            command.extend([ "-f", "--js", closure_deps ])

            for filename in inputs.keys():
                command.extend(['--namespace', n])

            for d in self.js_dirs:
                command.extend(["--root", d])

            cmd = Popen(
                command, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                universal_newlines=True
            )
            output, error = cmd.communicate()
            assert cmd.wait() == 0, 'Command returned bad result:\n%s' % error

            file_out = StringIO.StringIO()
            file_out.write(output)
            file_out.seek(0)

        except Exception, e:
            raise ValueError("Failed to execute closure-builder. "
                    "Please make sure that you have installed Python "
                    "and that it's in your PATH and that you've configured "
                    "CLOSURE_BUILDER_BINARY in your settings correctly.\n"
                    "Error was: %s" % e)

        #TODO:
        #It seems that the Closure compiler only ever returns 1 file
        #This is a bit odd.  TODO: check that this is right
        filename = inputs.keys()[0]
        outputs[filename] = file_out
        return outputs
