import os
from django.http import HttpResponse

from hashlib import md5
from ..base import Outputter
from google.appengine.api import files
from google.appengine.ext.blobstore import BlobInfo, BlobReader

class Blobstore(Outputter):
    def output(self, filename, file_out):
        content = file_out.read()
        hsh = md5(content).hexdigest()
        filename, ext = os.path.splitext(filename)
        out_filename = os.path.join(filename + "." + hsh + ext)

        if ext == ".css":
            mimetype = "text/css"
        elif ext == ".js":
            mimetype = "text/javascript"
        else:
            mimetype = "application/octet-stream"

        result = files.blobstore.create(mime_type=mimetype, _blobinfo_uploaded_filename=out_filename)
        with files.open(result, "a") as f:
            f.write(content)
        files.finalize(result)

        return self.url_root + out_filename

    def serve(self, filename):
        info = BlobInfo.all().filter('filename = ', filename).get()
        assert(info)
        content = BlobReader(info.key()).read()
        return HttpResponse(content, mimetype=info.content_type)
