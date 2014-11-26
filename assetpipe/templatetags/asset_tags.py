import os
from django import template
from django.conf import settings
from assetpipe.base import read_generated_media_file

IN_TESTING = getattr(settings, 'IN_TESTING', False)

register = template.Library()


class AssetNode(template.Node):
    def __init__(self, pipeline_name):
        self.pipeline_name = pipeline_name
        self._generated_cache = None

    def render(self, context):
        if IN_TESTING:
            return ''

        pipeline_name = template.Variable(self.pipeline_name).resolve(context)
        tags = []

        if settings.ASSET_DEV_MODE:
            active = settings.ASSET_PIPELINE_ACTIVE
            try:
                pipeline = settings.ASSET_PIPELINES[active][pipeline_name]
            except:
                raise template.TemplateSyntaxError(
                    "Pipeline with name %s not defined in settings.ASSET_PIPELINES." % pipeline_name
                )
            outputs = pipeline.output_urls()
        else:
            #On live, we used the generated media file
            if self._generated_cache is None:
                self._generated_cache = read_generated_media_file()

            outputs = self._generated_cache[pipeline_name]

        for output in outputs:
            if output.endswith(".css"):
                tag = u'<link rel="stylesheet" type="text/css" href="%s" />' % os.path.join(settings.STATIC_URL, output)
            elif output.endswith(".js"):
                tag = u'<script src="%s"></script>' % os.path.join(settings.STATIC_URL, output)
            else:
                raise ValueError("Invalid output found")
            tags.append(tag)
        return '\n'.join(tags)

@register.tag
def include_assets(parser, token):
    """ Template tag, {% include_assets "pipeline_name" %}. """
    try:
        contents = token.split_contents()
        pipeline_name = contents[1]
    except (ValueError, AssertionError, IndexError):
        raise template.TemplateSyntaxError(
            '%r could not parse the arguments: the first argument must be the '
            'the name of a file generated by the pipeline' % contents[0])

    return AssetNode(pipeline_name)

class AssetURLNode(template.Node):
    def __init__(self, pipeline_name):
        self.pipeline_name = pipeline_name
        self._generated_cache = None

    def render(self, context):
        if IN_TESTING:
            return ''

        pipeline_name = template.Variable(self.pipeline_name).resolve(context)

        if settings.ASSET_DEV_MODE:
            active = settings.ASSET_PIPELINE_ACTIVE
            try:
                pipeline = settings.ASSET_PIPELINES[active][pipeline_name]
            except:
                raise template.TemplateSyntaxError(
                    "Pipeline with name %s not defined in settings.ASSET_PIPELINES." % pipeline_name
                )
            outputs = pipeline.output_urls()
        else:
            #On live, we used the generated media file
            if self._generated_cache is None:
                self._generated_cache = read_generated_media_file()

            outputs = self._generated_cache[pipeline_name]

        if len(outputs) > 1:
            raise ValueError("Tried to access URL of a pipeline with multiple outputs")

        if outputs:
            return outputs[0]
        return ""

@register.tag
def asset_url(parser, token):
    """ Template tag, {% asset_urls "pipeline_name" %}. """
    try:
        contents = token.split_contents()
        pipeline_name = contents[1]
    except (ValueError, AssertionError, IndexError):
        raise template.TemplateSyntaxError(
            '%r could not parse the arguments: the first argument must be the '
            'the name of a file generated by the pipeline' % contents[0])

    return AssetURLNode(pipeline_name)