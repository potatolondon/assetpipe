import os
import glob
import logging

from .. import gae_sandbox
from .filesystem import Filesystem


class GaeFilesystem(Filesystem):
    """ File system-based outputter which works in the Google App Engine SDK. """

    def output(self, filename, file_out):
        content = file_out.read()

        base, ext = os.path.splitext(filename)

        already_exists = False
        #Remove any existing stale entries
        for f in glob.glob(os.path.join(self.directory, base.split(".")[0] + "*" + ext)):
            if f[len(self.directory):].lstrip("/") == filename:
                already_exists = True
                continue

            os.remove(f)

        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))

        if not already_exists:
            logging.info("Creating: %s", filename)

            with gae_sandbox.allow_writeable_filesystem():
                with open(filename, "w") as f:
                    f.write(content)
