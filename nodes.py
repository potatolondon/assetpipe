from collections import OrderedDict
import os
import StringIO
import glob
import logging
from django.conf import settings

from hashlib import md5

from .processors import (
    Bundle,
    ClosureBuilder,
    SCSS,
    YUI,
    ClosureCompiler
)

from .base import NullOutputter, NullProcessor #, NullCompiler, NullMinifier,
from .outputters.blobstore import Blobstore
from .outputters.filesystem import Filesystem

PROCESSORS = {}
OUTPUTTERS = {}

def register_processor(name, processor_class):
    PROCESSORS[name] = processor_class

def register_outputter(name, outputter_class):
    OUTPUTTERS[name] = outputter_class


register_processor("bundle", Bundle)
register_processor("closure_builder", ClosureBuilder)
register_processor("closure_compiler", ClosureCompiler)
register_processor("closure", ClosureCompiler)
register_processor("hashfilenames", NullProcessor)
register_processor("scss", SCSS)
register_processor("yui", YUI)

register_outputter("null", NullOutputter)
register_outputter("blobstore", Blobstore)
register_outputter("filesystem", Filesystem)


class Node(object):
    def __init__(self, parent):
        #the list of files (including wildcards) which we started with
        self._inputs = []

        #the expanded list of input files, with folder/* wildcards expanded
        self.input_files = []

        # filename:StringIO(contents) mappings of the files we will output
        # this is what gets modified in each step of the pipeline
        self.outputs = OrderedDict()

        self.output_filename_changes_done = False

        self.parent = parent
        self.child = None
        if parent:
            parent.child = self

    @property
    def inputs(self):
        if self.parent:
            return self.parent.outputs
        return self._inputs

    @property
    def head(self):
        if self.parent:
            return self.parent.head
        return self

    @property
    def tail(self):
        if self.child:
            return self.child.tail()
        return self

    def any_dirty(self):
        """ Does as much work as is necessary to find out if the pipeline needs to be run,
            but should avoid any expensive operations, because it needs to be run very often.
        """
        if self.is_dirty():
            return True

        if self.child:
            return self.child.any_dirty()
        else:
            return False

    def is_dirty(self):
        """ Return True if the pipeline should be run, False otherwise. """
        raise NotImplementedError()

    def prepare(self):
        """ Do necessary preparations the nodes need to be able to tell if the pipeline is dirty. """
        self.do_prepare()

        if self.child:
            self.child.prepare()

    def run(self):
        """ Starting point for the pipeline, calls prepare and any_dirty on the pipeline head
            If the pipeline is dirty, it calls _run on the head, to start the actual processing.
        """
        self.head.prepare()

        if self.head.any_dirty():
            logging.info("PIPELINE: Running pipeline")
            self.head._run()
        else:
            logging.info("PIPELINE: NOT running clean pipeline")

    def _run(self):
        """ Loop through all children and call do_run on each. """
        self.do_run()

        if self.child:
            self.child._run()

    def do_run(self):
        """ Perform the node's actions.
            This is called by _run, which loops through the pipeline.
        """
        raise NotImplementedError()

    #Generic methods which allow chaining of the nodes
    def Output(self, outputter, url_root=None, directory=None):
        url_root = url_root or settings.STATIC_URL
        return OutputNode(self, outputter, url_root, directory)

    def Process(self, processor, *args, **kwargs):
        return ProcessNode(self, processor, *args, **kwargs)


class OutputNode(Node):
    def __init__(self, parent, outputter_name, url_root, directory=None):
        super(OutputNode, self).__init__(parent)

        directory = os.path.join(settings.STATIC_ROOT, "")

        self.head.url_root = url_root
        self.outputter = OUTPUTTERS[outputter_name](directory)

    def output_urls(self):
        result = []

        output_dir = self.outputter.directory
        common_prefix = os.path.commonprefix([settings.STATIC_ROOT, output_dir])

        for (filename, content) in self.inputs.items():
            filename = self._add_hash_to_filename(filename)
            result.append(
                self.head.url_root +
                os.path.relpath(os.path.join(output_dir, filename), common_prefix)
            )
        return result

    def _add_hash_to_filename(self, filename):
        hsh = self.head.hash
        part, ext = os.path.splitext(filename)
        return ".".join([part, hsh, ext.lstrip(".")])

    def do_prepare(self):
        new_inputs = OrderedDict()
        for filename, contents in self.inputs.items():
            hashed_filename = self._add_hash_to_filename(filename)
            new_inputs[hashed_filename] = contents
        self._inputs = new_inputs

    def is_dirty(self):
        for filename, contents in self.inputs.items():
            filename = self._add_hash_to_filename(filename)
            if not self.outputter.file_up_to_date(filename):
                return True
        return False

    def do_run(self):
        #OutputNode is the only type of node which does not alter self.outputs
        for filename, contents in self.inputs.items():
            filename = self._add_hash_to_filename(filename)
            self.outputter.output(filename, contents)

    def serve(self, filename):
        return self.outputter.serve(filename)


class ProcessNode(Node):

    def __init__(self, parent, processor_name, *args, **kwargs):
        """ Instantiate the named processor passing in the pipeline and the given args and kwargs.
            Update the hash of the pipeline to include the fact that this processor has been added.
        """
        super(ProcessNode, self).__init__(parent)
        self.processor = PROCESSORS[processor_name](self.head, *args, **kwargs)

    def do_prepare(self):
        self.outputs = self.processor.prepare(self.inputs)

    def is_dirty(self):
        return False

    def do_run(self):
        self.outputs = self.processor.process(self.inputs)


class Gather(Node):
    """ The starting node of every pipeline.  Picks up the specified
        files from the filesystem and puts them into self.outputs.
    """
    def __init__(self, inputs, dependencies=[], filenames=True):
        super(Gather, self).__init__(None)

        #Try to glob match the inputs
        expanded_inputs = [] #will contain the full list of files, not just folder/*
        for inp in inputs:
            if filenames:
                #Deal with wildcards which refer to directories
                matches = glob.glob(inp)
                if matches:
                    expanded_inputs.extend(matches)
                else:
                    expanded_inputs.append(inp)
            else:
                expanded_inputs.append(inp)

        self.input_files = expanded_inputs if filenames else inputs
        self.input_files_are_filenames = filenames
        self.dependencies = dependencies

    def generate_hash(self, *args, **kwargs):
        parts = [ self.__class__.__name__ ] + [ str(x) for x in args ]
        for k in sorted(kwargs.keys()):
            parts.extend([k, str(kwargs[k]) ])

        hasher = md5()
        for part in parts:
            hasher.update(part)

        return hasher.hexdigest()

    def generate_pipeline_hash(self, inputs, dependencies=[], filenames=True):
        """
            Returns a hash representing this pipeline combined with its inputs
        """
        hasher = md5()
        for inp in sorted(inputs):
            if filenames:
                u = str(os.path.getmtime(inp))
                hasher.update(u)
            else:
                hasher.update(inp)

        # FIXME: Add dependency watching
        for dep in dependencies:
            # Update hasher for every file in dependencies
            pass
        return hasher.hexdigest()

    def do_prepare(self):
        # FIXME: This currently doesn't take into account the pipeline itself, the pipeline steps need to be included in the hash
        pipeline_hash = self.generate_pipeline_hash(self.input_files, dependencies=[], filenames=True)
        self.hash = self.generate_hash(*(self.input_files + [] + [pipeline_hash]))

    def is_dirty(self):
        outputs = OrderedDict()
        for inp in self.input_files:
            outputs[inp] = None
        self.outputs = outputs
        return False

    def do_run(self):
        """ Picks up file contents to start. """

        outputs = OrderedDict()
        for inp in self.input_files:
            if isinstance(inp, basestring):
                f = open(inp, "r")
                content = f.read()
                f.close()
            else:
                content = inp

            output = StringIO.StringIO()
            output.write(content)
            output.seek(0) #Rewind to the beginning
            outputs[inp] = output
        self.outputs = outputs
