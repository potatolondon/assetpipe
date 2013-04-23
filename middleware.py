from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed

class AssetMiddleware(object):
    def process_request(self, request):
        if not settings.DEBUG:
            raise MiddlewareNotUsed()

        active = getattr(settings, 'ASSET_PIPELINE_ACTIVE', 'DEV')
        pipelines = settings.ASSET_PIPELINES.get(active, {})

        for pipeline in pipelines.values():
            pipeline.run()

            url_root = pipeline._root().url_root

            if not request.path.startswith(url_root):
                #If the URL being requested is not a sub-path of the serving URL of this bundle
                continue

            #TODO: if we just made OutputNode.do_run() change self.outputs to the with-hash
            #versions of the file names then all this messing around here wouldn't be necessary

            #convert file-name.HASH12345XYZ.css into file-name.css
            filename_with_hash = request.path[len(url_root):]
            filename_base = filename_with_hash.split(".")

            parts = filename_base[0:-2]
            parts.append(filename_base[-1])
            filename_base = ".".join(parts)

            if filename_base in pipeline.outputs.keys():
                return pipeline.serve(filename_with_hash)
