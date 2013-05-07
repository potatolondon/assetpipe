# Asset Pipe

An extensible django library for processing and combining static web assets such as Javascript and CSS files.

Provides processors for SASS, Google Closure, and YUI compressor.  Can also be extended with your own processors.

For sites running on Google App Engine processed files are served from the Blobstore to circumvent not being able to write to the filesystem.

## Basic usage

Add the 'assetpipe' app to your Django project.

Define your piplines in settings.py...

```
ASSET_PIPELINES = {}
#For development we define our pipeline without the minification or bundle steps
ASSET_PIPELINES['dev'] = {
	"main_css": Gather(["base.scss", "style.scss"])
		.Process("scss")
		.Output("filesystem", os.path.join(PROJECT_DIR, "static", "js")),

	"main_js": Gather(["jquery.js", "custom.js"])
		.Output("blobstore", "/devmedia/"),
}
#For production we add in our minification and 'Bundle' steps
ASSET_PIPELINES['live'] = {
	"main_css": Gather(["base.scss", "style.scss"])
		.Process("scss")
		.Process("bundle", "admin.css") #the files will now be outputted as a single file with this name
		.Process("yui")
		.Output("filesystem", os.path.join(PROJECT_DIR, "static", "js")),

	"main_js": Gather(["jquery.js", "custom.js"])
		.Process("bundle", "main.js") #the files will now be outputted as a single file with this name
		.Process("yui")
		.Output("blobstore", "/devmedia/"),
}

ASSET_PIPELINE_ACTIVE = "live" if on_production_server else 'dev'

```

Then in your templates you can reference each set of assets by its key: `{% include_assets "main_css" %}`.  This will print out the `<link/>` or `<script/>` tag(s) for the pipeline.

There is a `genassets` management command which will run the pipeline you specify. For example, before deployment you will likely want to run your live asset pipeline, you can do so by
runing the following command:

`python manage.py genassets --pipeline live`

# Registering your own processors

To write your own processor you must subclass `assetpipe.base.Processor`. This has two methods that must be overridden. The most important one is "process" which takes an ordered dictionary of
{ filename : file_like_object } which are the outputs from the previous stage in the pipeline. Your process function should manipulate these inputs in some way and then return another OrderedDict
of filenames and files ready for the next stage in the pipeline.

The other method that you should override is modify_expected_output_filenames(). If your processor will manipulate the input filenames before passing to the next stage, then you should do that
manipulation in this method. This is so that the include_assets template tag knows what to include.

Once you have defined your Processor subclass, you must register it before it can be run. You can do this with the assetpipe.base.register_processor function:

    register_processor("my_processor", MyProcessor)

After this, you'll be able to call your processor in a pipeline, e.g.

    Gather().Process("my_processor").Output()


# Settings

    ASSET_DEV_MODE = True|False

If True, then the pipeline middleware will run on each request, this should be switched off on production

    ASSET_PIPELINE_ACTIVE = str

This defines which of the pipelines is "active" and will be run by the assetpipe middleware

    ASSET_PIPELINES = { pipeline_name: { bundle_name: Pipeline } }

This is the main setting, it defines your pipelines, it's a dictionary of dictionaries where the
value is the pipeline itself

## SASS Settings

    SASS_ADDITIONAL_LOAD_PATHS = [ str, str ... ]

This is a list of paths that will be added to Ruby's load path before executing SASS

    SASS_ADDITIONAL_INCLUDE_PATHS = [ str, str ... ]

This is a list of include directories that will be passed to SASS

    SASS_ADDITIONAL_REQUIRES = [ str, str ... ]

This is a list of Ruby modules that will be passed to SASS with --require

    SASS_COMPILER_BINARY = str

The path to the sass executable

## YUI Settings

    YUI_COMPRESSOR_BINARY = str

The path to the yuicompressor JAR file

## Closure Settings

    CLOSURE_BUILDER_BINARY = str

The path to the closurebuilder script. This must be in the closure-library tree for this processor to work.

## Djangoappengine Settings

With the latest djangoappengine from the potatolondon GitHub, you can use the following:

    PRE_DEPLOY_COMMANDS = (
        ('genassets', [], {"pipeline" : "live"}),
    )

which will generate your live assets at deploy time.
