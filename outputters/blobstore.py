import os
import logging

from django.http import HttpResponse, HttpResponseNotFound
from django.conf import settings

from ..base import Outputter
try:
    #Import the Google App Engine Blobstore if we have it
    #but don't die (yet) if we don't.
    from google.appengine.api import files
    from google.appengine.ext.blobstore import BlobInfo, BlobReader
    HAVE_BLOBSTORE = True
except ImportError:
    HAVE_BLOBSTORE = False


class Blobstore(Outputter):

    def __init__(self, directory=None, strip_path=None, *args, **kwargs):
        if not HAVE_BLOBSTORE:
            raise ImproperlyConfigured(
                "Google Appengine components required for the 'blobstore' "
                "outputter could not be imported."
            )        
        super(Blobstore, self).__init__(directory, strip_path)

    def output(self, filename, file_out):
        if filename.startswith(settings.STATIC_ROOT):
            filename = filename[len(settings.STATIC_ROOT) + 1:]

        content = file_out.read()

        base, ext = os.path.splitext(filename)

        if ext == ".css":
            mimetype = "text/css"
        elif ext == ".js":
            mimetype = "text/javascript"
        elif ext == ".png":
            mimetype = "image/png"    
        else:
            mimetype = "application/octet-stream"

        already_exists = False

        for info in BlobInfo.all().filter('content_type = ', mimetype):
            if info.filename == filename:
                already_exists = True
                continue

            #Clear out old blobs
            if info.filename.split(".")[0] == filename.split(".")[0]:
                logging.debug("Deleting: %s", info.filename)
                info.delete()

        if not already_exists:
            logging.info("Creating: %s", filename)
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
        #TODO: Surely if this file is served from a hash-based URL then we
        #can return HTTP caching headers, right?
        info = BlobInfo.all().filter('filename = ', filename).get()
        if not info:
            return HttpResponseNotFound()
            #
        content = BlobReader(info.key()).read()
        return HttpResponse(content, mimetype=info.content_type)
