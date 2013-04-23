# TODO

* Now that the .Minify(), .Bundle(), .Compile() steps are all very similar, we should be able to just make them into a generic .Process() step, so that custom processors of any kind can be written and used.  E.g. `Gather("file.js", "file2.js").Process("scss").Process("yui").Process("bundle", "scripts.js").Output("blobstore")`.
