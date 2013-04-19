import os
import logging

from django.http import HttpResponse, HttpResponseNotFound

from ..base import Outputter
from google.appengine.api import files
from google.appengine.ext.blobstore import BlobInfo, BlobReader

class Blobstore(Outputter):
    def output(self, filename, file_out):
        content = file_out.read()

        base, ext = os.path.splitext(filename)

        if ext == ".css":
            mimetype = "text/css"
        elif ext == ".js":
            mimetype = "text/javascript"
        else:
            mimetype = "application/octet-stream"

        already_exists = False

        for info in BlobInfo.all().filter('content_type = ', mimetype):
            if info.filename == filename:
                already_exists = True
                continue

            #Clear out old blobs
            if info.filename.split(".")[0] == filename.split(".")[0]:
                logging.error("Deleting: %s", info.filename)
                info.delete()

        if not already_exists:
            logging.error("Creating: %s", filename)
            result = files.blobstore.create(mime_type=mimetype, _blobinfo_uploaded_filename=filename)
            with files.open(result, "a") as f:
                f.write(content)
            files.finalize(result)

            blob_key = files.blobstore.get_blob_key(result)
            while not blob_key:
                blob_key = files.blobstore.get_blob_key(result)

    def file_up_to_date(self, filename):
        result = bool(BlobInfo.all().filter('filename =', filename).count())
        return result

    def serve(self, filename):
        info = BlobInfo.all().filter('filename = ', filename).get()
        if not info:
            return HttpResponseNotFound()
            #
        content = BlobReader(info.key()).read()
        return HttpResponse(content, mimetype=info.content_type)
