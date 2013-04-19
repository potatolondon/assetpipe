import os
import StringIO
from ..base import Compiler
from djangoappengine.boot import PROJECT_DIR

from django.conf import settings

SASS_INCLUDE_PATHS = [
    os.path.join(PROJECT_DIR, "gems", "sass", "lib"),
    os.path.join(PROJECT_DIR, "gems", "compass", "lib"),
    os.path.join(PROJECT_DIR, "gems", "chunky_png", "lib"),
    os.path.join(PROJECT_DIR, "gems", "rubygems", "lib"),
]

SASS_FRAMEWORKS = [
    os.path.join(PROJECT_DIR, "gems", "compass", "frameworks", "compass", "stylesheets"),
    os.path.join(PROJECT_DIR, "gems", "compass", "frameworks", "blueprint", "stylesheets"),
]

SASS_COMPILER_BINARY = os.path.join(PROJECT_DIR, "gems", "sass", "bin", "sass")

class SCSS(Compiler):
    def compile(self, inputs):
        from subprocess import Popen, PIPE

        results = []

        sass_path = SASS_COMPILER_BINARY

        command = [ "ruby" ]

        for path in SASS_INCLUDE_PATHS:
            command.append("-I")
            command.append('%s' % path)

        command.append(sass_path.strip())
        command.extend(["-C", "-t", "expanded", "-s", "--require", "compass" ])

        if settings.DEBUG:
            command.append("--line-numbers")

        for path in SASS_FRAMEWORKS:
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

