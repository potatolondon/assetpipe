from collections import OrderedDict
import os
import StringIO
import glob
import logging
import re
import time

from django.utils import timezone
from django.conf import settings

from hashlib import md5

from .processors import (
    Bundle,
    ClosureBuilder,
    HashFileNames,
    SCSS,
    YUI,
    ClosureCompiler
)

from .base import NullOutputter #, NullCompiler, NullMinifier,
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
register_processor("hashfilenames", HashFileNames)
register_processor("scss", SCSS)
register_processor("yui", YUI)

register_outputter("null", NullOutputter)
register_outputter("blobstore", Blobstore)
register_outputter("filesystem", Filesystem)


class Node(object):
    def __init__(self, parent):
        #the list of files (including wildcards) which we started with
        self.inputs = []

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


    def _root(self):
        if self.parent:
            return self.parent._root()
        return self

    def prepare(self):
        """ A bit like calling .run() but without the is_dirty() checks. """
        self.run_output_filename_changes()
        self.output_filename_changes_done = True

    def run(self):
        if not self.output_filename_changes_done:
            self.run_output_filename_changes()
            self.output_filename_changes_done = True
        if self.any_dirty():
            self.run_output_filename_changes()
            logging.info("PIPELINE: Running pipeline")
            self._root()._run()

    def _run(self):
        if self.parent:
            self.outputs = self.parent.outputs.copy()

        self.do_run()

        if self.child:
            self.child._run()

    def do_run(self):
        """ Alter self.outputs. """
        raise NotImplementedError()

    def is_dirty(self): raise NotImplementedError()

    def modify_expected_output_filenames(self):
        """ Alter self.expected_output_filenames in the same way that they
            will be modified by do_run() when the pipeline actually runs.
        """
        raise NotImplementedError()

    def any_dirty(self):
        n = self._root()
        while n.child:
            if n.is_dirty():
                return True
            n = n.child

        return n.is_dirty()

    def run_output_filename_changes(self):
        n = self._root()
        n.expected_output_filenames = []
        while n.child:
            n.modify_expected_output_filenames()
            n.child.expected_output_filenames = n.expected_output_filenames
            n = n.child
        n.modify_expected_output_filenames()

    def generate_pipeline_hash(self, inputs, filenames=True):
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
        return hasher.hexdigest()


    def update_hash(self, *args, **kwargs):
        parts = [ self.__class__.__name__ ] + [ str(x) for x in args ]
        for k in sorted(kwargs.keys()):
            parts.extend([k, str(kwargs[k]) ])

        hasher = md5()
        for part in parts:
            hasher.update(part)

        self.hash = hasher.hexdigest()

    #Generic methods which allow chaining of the nodes
    def Output(self, outputter, url_root=None, directory=None):
        url_root = url_root or settings.STATIC_URL
        return OutputNode(self, outputter, url_root, directory)

    def Process(self, processor, *args, **kwargs):
        return ProcessNode(self, processor, *args, **kwargs)

    def Watch(self, *args, **kwargs):
        return Watch(self, *args, **kwargs)


class OutputNode(Node):
    def __init__(self, parent, outputter_name, url_root, directory=None):
        super(OutputNode, self).__init__(parent)

        directory = os.path.join(settings.STATIC_ROOT, directory or "")

        self.update_hash(parent, outputter_name, url_root, directory)

        self._root().url_root = url_root
        self.outputter = OUTPUTTERS[outputter_name](directory)


    def output_urls(self):
        result = []

        output_dir = self.outputter.directory
        common_prefix = os.path.commonprefix([settings.STATIC_ROOT, output_dir])

        for output in self.expected_output_filenames:
            result.append(
                self._root().url_root +
                os.path.relpath(os.path.join(output_dir, output), common_prefix)
            )

        return result

    def modify_expected_output_filenames(self):
        pass

    def do_run(self):
        #OutputNode is the only type of node which does not alter self.outputs
        for filename, contents in self.outputs.items():
            self.outputter.output(filename, contents)

    def serve(self, filename):
        return self.outputter.serve(filename)

    def is_dirty(self):
        for f in self.expected_output_filenames:
            if not self.outputter.file_up_to_date(f):
                return True
        return False


class ProcessNode(Node):

    def __init__(self, parent, processor_name, *args, **kwargs):
        """ Instantiate the named processor passing in the pipeline and the given args and kwargs.
            Update the hash of the pipeline to include the fact that this processor has been added.
        """
        super(ProcessNode, self).__init__(parent)
        self.update_hash(parent, processor_name, *args, **kwargs)
        self.processor = PROCESSORS[processor_name](self._root(), *args, **kwargs)

    def modify_expected_output_filenames(self):
        self.expected_output_filenames = self.processor.modify_expected_output_filenames(
            self.expected_output_filenames
        )

    def do_run(self):
        self.outputs = self.processor.process(self.outputs)

    def is_dirty(self):
        return False


class Watch(Node):
    def __init__(self, parent, to_watch, filter_files, *args, **kwargs):
        super(Watch, self).__init__(parent, *args, **kwargs)
        self.watcher_id = hash(''.join(self.inputs))
        self.filter = filter_files

        # Separate to_watch list into files and directories for easier processing later on
        self.files_to_watch = []
        self.dirs_to_watch = []
        for file_or_dir in to_watch:
            if os.path.isdir(file_or_dir):
                self.dirs_to_watch.append(file_or_dir)
            else:
                self.files_to_watch.append(file_or_dir)

    @property
    def metadata(self):
        """ This is a bit hacky, but necessary to avoid a circular import with the settings file """
        if not hasattr(self, "_metadata"):
            from .models import WatcherMetadata
            self._metadata = WatcherMetadata.objects.get_or_create(watcher_id=self.watcher_id)[0]
        return self._metadata

    def modify_expected_output_filenames(self):
        pass

    def do_run(self):
        self.metadata.last_run_at = timezone.now()
        self.metadata.save()

    def check_file_modified(self, file):
        last_run = self.metadata.last_run_at
        if not last_run or os.path.getmtime(file) > time.mktime(last_run.timetuple()):
            return True
        return False

    def is_dirty(self):
        for f in self.files_to_watch:
            pass

        for directory in self.dirs_to_watch:
            for root, subFolders, files in os.walk(directory):
                for f in [x for x in files if re.search(self.filter, x)]:
                    if not root.endswith("/"):
                        root += "/"

                    full_path = root + f
                    if self.check_file_modified(full_path):
                        return True
        return False


class Gather(Node):
    """ The starting node of every pipeline.  Picks up the specified
        files from the filesystem and puts them into self.outputs.
    """
    def __init__(self, inputs, filenames=True):
        super(Gather, self).__init__(None)

        self.update_hash(inputs, filenames)

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
        self.pipeline_hash = self.generate_pipeline_hash(self.input_files, self.input_files_are_filenames)

    def modify_expected_output_filenames(self):
        if self.input_files_are_filenames:
            self.expected_output_filenames = self.input_files
        else:
            #Currently the CompileNode can take Closure namespaces instead of files :-/
            raise NotImplementedError("What do we do here?")

    def do_run(self):
        """ Picks up file contents to start.
        """
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

    def is_dirty(self):
        self.pipeline_hash = self.generate_pipeline_hash(self.input_files, self.input_files_are_filenames)
        self.prepare()
        return False
