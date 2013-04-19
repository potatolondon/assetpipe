import os
import StringIO
from ..base import Compiler

from django.conf import settings

class SCSS(Compiler):
    def compile(self, inputs):
        from subprocess import Popen, PIPE

        results = []

        sass_path = settings.SASS_COMPILER_BINARY

        command = [ "ruby" ]

        for path in getattr(settings, "SASS_ADDITIONAL_LOAD_PATHS", []):
            command.append("-I")
            command.append('%s' % path)

        command.append(sass_path.strip())
        command.extend(["-C", "-t", "expanded", "-s"])

        for require in getattr(settings, "SASS_ADDITIONAL_REQUIRES", []):
            command.extend(["--require", require ])

        if settings.DEBUG:
            command.append("--line-numbers")

        for path in getattr(settings, "SASS_ADDITIONAL_INCLUDE_PATHS", []):
            command.append("-I")
            command.append('%s' % path)

        try:
            for i, inp in enumerate(inputs):
                #Ignore CSS files, they don't need compiling
                f, ext = os.path.splitext(inp)
                if ext == ".css": continue

                cmd = Popen(
                    command,
                    stdin=PIPE, stdout=PIPE, stderr=PIPE,
                    universal_newlines=True
                )

                output, error = cmd.communicate('@import "%s"' % inp)
                assert cmd.wait() == 0, 'Command returned bad result:\n%s' % error

                file_out = StringIO.StringIO()
                file_out.write(output)
                file_out.seek(0)
                results.append(file_out)

        except Exception, e:
            raise ValueError("Failed to execute Ruby or SASS. "
                    "Please make sure that you have installed Ruby "
                    "and that it's in your PATH and that you've configured "
                    "SASS_COMPILER_BINARY in your settings correctly.\n"
                    "Error was: %s" % e)

        return results

