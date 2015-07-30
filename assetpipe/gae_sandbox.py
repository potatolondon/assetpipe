""" Utilities for allowing assetpipe to work in the Google App Engine SDK. """

import contextlib
try:
    from google.appengine.tools.devappserver2.python import stubs
    ON_GAE = True
except ImportError:
    ON_GAE = False


if ON_GAE:
    def allow_modules(func):
        """
            A decorator for allowing modules that are usually disallowed by App Engine.
            dev_appserver likes to kill your imports with meta_path madness so you
            use the internal ones instead of system ones, this wrapper reloads the
            modules and patches the google internal ones with the __dict__ from the
            system modules, this seems to be the cleanest way to do this even though
            it is a bit hacky
        """
        def _wrapped(*args, **kwargs):
            import sys

            import subprocess
            import os
            import tempfile
            import select
            # Clear the meta_path so google does not screw our imports, make a copy
            # of the old one
            old_meta_path = sys.meta_path
            sys.meta_path = []
            patch_modules = [os, tempfile, select, subprocess]

            import copy
            environ = copy.copy(os.environ)

            for mod in patch_modules:
                _system = reload(mod)
                mod.__dict__.update(_system.__dict__)

            # We have to maintain the environment, or bad things happen
            os.environ = environ

            try:
                return func(*args, **kwargs)
            finally:
                # Restore the original path
                sys.meta_path = old_meta_path
                # Reload the original modules
                for mod in patch_modules:
                    _system = reload(mod)
                    mod.__dict__.update(_system.__dict__)
                # Put the environment back, again
                os.environ = environ


        return _wrapped


    @contextlib.contextmanager
    def allow_writeable_filesystem():
        original_modes = stubs.FakeFile.ALLOWED_MODES
        new_modes = set(stubs.FakeFile.ALLOWED_MODES)
        new_modes.add('w')
        new_modes.add('wb')
        stubs.FakeFile.ALLOWED_MODES = frozenset(new_modes)
        try:
            yield
        finally:
            stubs.FakeFile.ALLOWED_MODES = original_modes

else:
    # Not on App Engine, provide no-ops
    def allow_modules(func):
        return func

    @contextlib.contextmanager
    def allow_writeable_filesystem():
        yield
