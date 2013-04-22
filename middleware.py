from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed

class AssetMiddleware(object):
    def process_request(self, request):
        if not settings.DEBUG:
            raise MiddlewareNotUsed()

        pipelines = getattr(settings, 'ASSET_PIPELINES', {})

        for pipeline in pipelines.get(getattr(settings, 'ASSET_PIPELINE_ACTIVE'), 'DEV'):
            pipeline.run()

            url_root = pipeline._root().url_root

            if not request.path.startswith(url_root):
                continue

            filename = request.path[len(url_root):]

            bundle_name = filename.split(".")
            bundle_name = ".".join([bundle_name[0], bundle_name[-1]])

            if bundle_name in pipeline._root().generated_files:
                return pipeline.serve(filename)
