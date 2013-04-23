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

            filename = request.path[len(url_root):]
            if filename in pipeline.expected_output_filenames:
                return pipeline.serve(filename)
