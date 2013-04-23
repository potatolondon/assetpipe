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
ASSET_PIPELINES['DEV'] = {
	"main_css": Gather(["base.scss", "style.scss"])
		.Compile("scss")
		.Output("filesystem", os.path.join(PROJECT_DIR, "static", "js")),

	"main_js": Gather(["jquery.js", "custom.js"])
		.Output("blobstore", "/devmedia/"),
]
#For production we add in our minification and 'Bundle' steps
ASSET_PIPELINES['LIVE'] = {
	"main_css": Gather(["base.scss", "style.scss"])
		.Compile("scss")
		.Bundle("admin.css") #the files will now be outputted as a single file with this name
		.Minify("yui")
		.Output("filesystem", os.path.join(PROJECT_DIR, "static", "js")),

	"main_js": Gather(["jquery.js", "custom.js"])
		.Bundle("main.js") #the files will now be outputted as a single file with this name
		.Minify("yui")
		.Output("blobstore", "/devmedia/"),
}
```

Then in your templates you can reference each set of assets by its key: `{% include_assets "main_css" %}`.  This will print out the `<link/>` or `<script/>` tag(s) for the pipeline.

There is a `genassets` management command which will run the live pipelines


