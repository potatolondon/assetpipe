from collections import OrderedDict
import os
import StringIO
import logging

from ..base import Processor

from django.conf import settings

class SCSS(Processor):
    def __init__(self, pipeline, use_compass=False, debug=False, *args, **kwargs):
        super(SCSS, self).__init__(pipeline, *args, **kwargs)
        self.debug = debug
        self.use_compass = use_compass

    def process(self, inputs):
        from subprocess import Popen, PIPE

        outputs = OrderedDict()

        sass_path = settings.SASS_COMPILER_BINARY

        command = [ "ruby" ]

        for path in getattr(settings, "SASS_ADDITIONAL_LOAD_PATHS", []):
            command.append("-I")
            command.append('%s' % path)

        command.append(sass_path.strip())
        command.extend(["-C", "-t", "expanded", "-s"])

        if self.use_compass:
            command.append("--compass")

        for require in getattr(settings, "SASS_ADDITIONAL_REQUIRES", []):
            command.extend(["--require", require ])

        if settings.DEBUG:
            command.append("--line-numbers")

        for path in getattr(settings, "SASS_ADDITIONAL_INCLUDE_PATHS", []):
            command.append("-I")
            command.append('%s' % path)

        if self.debug:
            command.append("--debug-info")

        try:
            for filename, contents in inputs.items():
                #Ignore CSS files, they don't need compiling
                f, ext = os.path.splitext(filename)
                if ext == ".css":
                    outputs[filename] = contents
                    continue

                cmd = Popen(
                    command,
                    stdin=PIPE, stdout=PIPE, stderr=PIPE,
                    universal_newlines=True
                )

                filename = filename.replace("\\", "/")
                output, error = cmd.communicate('@import "%s"' % filename)

                if error:
                    logging.warn(error)

                assert cmd.wait() == 0, 'Command returned bad result:\n%s' % error

                file_out = StringIO.StringIO()
                file_out.write(output)
                file_out.seek(0)
                #alter the filename to change the .scss extension to .css now that we've compiled it
                filename = "%s.css" % f
                outputs[filename] = file_out

        except Exception, e:
            raise ValueError("Failed to execute Ruby or SASS. "
                    "Please make sure that you have installed Ruby "
                    "and that it's in your PATH and that you've configured "
                    "SASS_COMPILER_BINARY in your settings correctly.\n"
                    "Error was: %s" % e)
        return outputs
