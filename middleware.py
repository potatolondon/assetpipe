from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed

IN_TESTING = getattr(settings, 'IN_TESTING', False)


class AssetMiddleware(object):
    def __init__(self):
        if not settings.ASSET_DEV_MODE:
            raise MiddlewareNotUsed()
        else:
            from django.core.exceptions import ImproperlyConfigured
            #Check all the settings are available
            required_settings = [
                "ASSET_MEDIA_URLS_FILE",
                "ASSET_DEV_MODE",
                "ASSET_PIPELINE_ACTIVE",
                "ASSET_PIPELINES"
            ]

            for setting_name in required_settings:
                setting = getattr(settings, setting_name, None)
                if setting is None:
                    raise ImproperlyConfigured("Missing assetpipe setting '%s'" % setting_name)

    def process_request(self, request):
        active = getattr(settings, 'ASSET_PIPELINE_ACTIVE')
        pipelines = settings.ASSET_PIPELINES.get(active, {})

        if IN_TESTING:
            return
        for pipeline in pipelines.values():
            pipeline.run()
            url_root = pipeline.head.url_root

            if not request.path.startswith(url_root):
                #If the URL being requested is not a sub-path of the serving URL of this bundle
                continue

            filename = request.path[len(url_root):]
            return pipeline.serve(filename)
