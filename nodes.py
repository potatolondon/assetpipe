import os
import StringIO
import glob

from .compilers.scss import SCSS
from .compilers.closure import Closure
from .minifiers.yui import YUI

from .outputters.blobstore import Blobstore
from .outputters.filesystem import Filesystem

COMPILERS = {}
MINIFIERS = {}
OUTPUTTERS = {}

COMPILERS_BY_EXTENSION = {}

def register_compiler(name, compiler_class, extensions=None):
    COMPILERS[name] = compiler_class
    if extensions:
        for ext in extensions:
            COMPILERS_BY_EXTENSION[ext.lstrip(".")] = compiler_class

def register_minifier(name, minifier_class):
    MINIFIERS[name] = minifier_class

def register_outputter(name, outputter_class):
    OUTPUTTERS[name] = outputter_class

register_compiler("scss", SCSS, [".scss"])
register_compiler("closure", Closure)

register_minifier("yui", YUI)

register_outputter("blobstore", Blobstore)
register_outputter("filesystem", Filesystem)

class Node(object):
    def __init__(self, parent):
        self.inputs = []
        self.outputs = []

        self.parent = parent
        self.child = None
        if parent:
            parent.child = self

    def _root(self):
        if self.parent:
            return self.parent._root()
        return self

    def run(self):
        self._root()._run()

    def _run(self):
        if self.parent:
            self.inputs = self.parent.outputs

        self.outputs = []
        self.do_run()

        if self.child:
            self.child._run()

    def do_run(self):
        raise NotImplementedError()

class OutputNode(Node):
    def __init__(self, parent, outputter_name, url_root, directory=None):
        super(OutputNode, self).__init__(parent)
        self._root().url_root = url_root
        self.outputter = OUTPUTTERS[outputter_name](url_root, directory)

    def do_run(self):
        for filename, f in zip(self._root().generated_files, self.inputs):
            self.outputs.append(self.outputter.output(filename,f))

    def serve(self, filename):
        return self.outputter.serve(filename)

class MinifyNode(Node):
    def __init__(self, parent, minifier):
        super(MinifyNode, self).__init__(parent)

        self.minifier_name = minifier

    def Output(self, outputter, directory=None):
        return OutputNode(self, outputter, directory)

    def do_run(self):
        filetypes = [ os.path.splitext(x)[-1].lstrip(".") for x in self._root().generated_files ]
        self.outputs = MINIFIERS[self.minifier_name]().minify(filetypes, self.inputs)

class BundleNode(Node):
    def __init__(self, parent, output_file):
        super(BundleNode, self).__init__(parent)

        #Overwrite the generated_files list with just the single output file
        self._root().generated_files = [ output_file ]
        self.output_file = output_file

    def Minify(self, minifier):
        return MinifyNode(self, minifier)

    def Output(self, outputter, url_root=None, directory=None):
        from django.conf import settings
        url_root = url_root or settings.STATIC_URL

        return OutputNode(self, outputter, url_root, directory)

    def do_run(self):
        """
            Concatenates the input filestreams into a single StringIO and then
            passes it on
        """

        output = StringIO.StringIO()
        for inp in self.inputs:
            if isinstance(inp, basestring):
                inp = open(inp, "r")

            content = inp.read()
            output.write(content)
            inp.close()

        output.seek(0) #Rewind to the beginning
        self.outputs = [ output ]

class CompileNode(Node):
    def __init__(self, parent, compiler_name, **kwargs):
        super(CompileNode, self).__init__(parent)

        self.kwargs = kwargs
        self.compiler_name = compiler_name

    def Bundle(self, output_name):
        return BundleNode(self, output_name)

    def Output(self, outputter, url_root=None, directory=None):
        from django.conf import settings
        url_root = url_root or settings.STATIC_URL
        return OutputNode(self, outputter, url_root, directory)

    def do_run(self):
        if self.compiler_name:
            compiler = COMPILERS[self.compiler_name](**self.kwargs)
        else:
            filename, ext = os.path.splitext(self.inputs[0])
            ext = ext.lstrip(".")

            if ext in COMPILERS_BY_EXTENSION:
                compiler = COMPILERS_BY_EXTENSION[ext](**self.kwargs)
            else:
                raise ValueError("Couldn't find compiler for extension: '%s'" % ext)

        self.outputs = compiler.compile(self.inputs)

class Gather(Node):
    def __init__(self, inputs):
        super(Gather, self).__init__(None)

        #Try to glob match the inputs
        for inp in inputs:
            if "*" in inp or "?" in inp or "[" in inp:
                matches = glob.glob(inp)
                if matches:
                    self.inputs.extend(matches)
            else:
                self.inputs.append(inp)

        self.generated_files = self.inputs

    def do_run(self):
        self.outputs = self.inputs

    def Compile(self, compiler_name=None, **kwargs):
        return CompileNode(self, compiler_name, **kwargs)

    def Bundle(self, output_name):
        return BundleNode(self, output_name)
