

class Compiler(object):
    def __init__(self, *args, **kwargs):
        pass

    def compile(self, inputs):
        raise NotImplementedError()

class Minifier(object):
    def minify(self, inputs):
        raise NotImplementedError()

class Outputter(object):
    def __init__(self, directory=None):
        self.directory = directory

    def output(self, filename, file_out):
        raise NotImplementedError()

class NullCompiler(object):
    def compile(self, inputs):
        return inputs

class NullMinifier(object):
    def minify(self, filetypes, inputs):
        return inputs

class NullOutputter(object):
    def __init__(self, directory):
        self.cache = set()

    def output(self, filename, file_out):
        self.cache.add(filename)

    def file_up_to_date(self, filename):
        return filename in self.cache
