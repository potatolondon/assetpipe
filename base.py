

class Compiler(object):
    def compile(self, inputs):
        raise NotImplementedError()

class Minifier(object):
    def minify(self, inputs):
        raise NotImplementedError()

class Outputter(object):
    def __init__(self, url_root, directory=None):
        self.url_root = url_root
        self.directory = directory

    def output(self, filename, file_out):
        raise NotImplementedError()

