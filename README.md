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
		.Compile("scss")
		.Output("filesystem", os.path.join(PROJECT_DIR, "static", "js")),

	"main_js": Gather(["jquery.js", "custom.js"])
		.Output("blobstore", "/devmedia/"),
]
#For production we add in our minification and 'Bundle' steps
ASSET_PIPELINES['live'] = {
	"main_css": Gather(["base.scss", "style.scss"])
		.Compile("scss")
		.Bundle("admin.css") #the files will now be outputted as a single file with this name
		.Compress("yui")
		.Output("filesystem", os.path.join(PROJECT_DIR, "static", "js")),

	"main_js": Gather(["jquery.js", "custom.js"])
		.Bundle("main.js") #the files will now be outputted as a single file with this name
		.Compress("yui")
		.Output("blobstore", "/devmedia/"),
}

ASSET_PIPELINE_ACTIVE = "live" if on_production_server else 'dev'

```

Then in your templates you can reference each set of assets by its key: `{% include_assets "main_css" %}`.  This will print out the `<link/>` or `<script/>` tag(s) for the pipeline.

There is a `genassets` management command which will run the pipeline you specify. For example, before deployment you will likely want to run your live asset pipeline, you can do so by
runing the following command:

`python manage.py genassets --pipeline live`

# Registering your own processors

The Compile, Bundle, Compress and Hash functions are just logical wrappers around the built-in "Process" command. Each stage of the pipeline aside from Gather and Output is a generic "processor".

To clarify, the above example could also be written like this, where the first argument to Process defines which processor to use:

ASSET_PIPELINES['live'] = {
	"main_css": Gather(["base.scss", "style.scss"])
		.Process("scss")
		.Process("bundle", "admin.css")
		.Process("yui")
		.Output("filesystem", os.path.join(PROJECT_DIR, "static", "js"))
}

To write your own processor you must subclass `assetpipe.base.Processor`. This has two methods that must be overridden. The most important one is "process" which takes an ordered dictionary of
{ filename : file_like_object } which are the outputs from the previous stage in the pipeline. Your process function should manipulate these inputs in some way and then return another OrderedDict
of filenames and files ready for the next stage in the pipeline.

The other method that you should override is modify_expected_output_filenames(). If your processor will manipulate the input filenames before passing to the next stage, then you should do that
manipulation in this method. This is so that the include_assets template tag knows what to include.

Once you have defined your Processor subclass, you must register it before it can be run. You can do this with the assetpipe.base.register_processor function:

    register_processor("my_processor", MyProcessor)

After this, you'll be able to call your processor in a pipeline, e.g.

    Gather().Process("my_processor").Output()

If you want, you can give your processor a stage. For example, if your processor is a compiler of some sort, you can do this instead:

    register_processor("my_processor", MyProcessor, stage="Compile")
    Gather().Compile("my_processor").Output()

