import os
import StringIO
from django.conf import settings
from ..base import Compiler

class Closure(Compiler):
    def __init__(self, js_dirs):
        self.js_dirs = js_dirs

    def compile(self, inputs):
        assert(inputs)
        assert(self.js_dirs)

        from subprocess import Popen, PIPE

        results = []

        builder = settings.CLOSURE_BUILDER_BINARY
        try:
            command = ['python', builder, "--output_mode", "script" ]

            closure_dir = os.path.dirname(os.path.dirname(os.path.dirname(builder)))
            closure_deps = "%s/goog/deps.js" % closure_dir
            assert(os.path.exists(closure_deps))

            command.extend([ "-f", "--js", closure_deps ])

            for n in inputs:
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
            results.append(file_out)

        except Exception, e:
            raise ValueError("Failed to execute closure-builder. "
                    "Please make sure that you have installed Python "
                    "and that it's in your PATH and that you've configured "
                    "CLOSURE_BUILDER_BINARY in your settings correctly.\n"
                    "Error was: %s" % e)

        return results
