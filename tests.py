import os
import time
import tempfile

from django.test import TestCase
from .nodes import Gather

def touch(fname, times=None):
    open(fname, 'a').close()
    os.utime(fname, None)

class CacheTest(TestCase):
    def test_caching_of_output(self):
        path = os.path.join(tempfile.gettempdir(), "test")
        touch(path)

        pipeline = Gather([path]).Compile("null").Bundle("thing.css").Minify("null").Output("null", "/devmedia/")

        self.assertTrue(pipeline.any_dirty()) #Should be dirty to begin with

        pipeline.run()

        self.assertFalse(pipeline.any_dirty()) #Not dirty

        time.sleep(1)
        touch(path)

        self.assertTrue(pipeline.any_dirty()) #Dirty again

        pipeline.run()

        self.assertFalse(pipeline.any_dirty()) #Not dirty
