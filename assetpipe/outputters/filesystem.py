import os
import sys
import glob
import logging
from django.http import HttpResponse

from ..base import Outputter

class Filesystem(Outputter):
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

            with open(filename, "w") as f:
                f.write(content)

    def file_up_to_date(self, filename):
        #FIXME: Check timestamp instead of returning false for images
        if filename.endswith(".png") or filename.endswith(".gif"):
            return False

        #Always return false if we are manually generating
        if "genassets" in sys.argv:
            return False

        return os.path.exists(filename)

    def serve(self, filename):
        base, ext = os.path.splitext(filename)

        if ext == ".css":
            mimetype = "text/css"
        elif ext == ".js":
            mimetype = "text/javascript"
        else:
            mimetype = "application/octet-stream"

        content = open(filename, "r").read()

        return HttpResponse(content, mimetype=mimetype)
