import os

from ..base import Compiler
from djangoappengine.boot import PROJECT_DIR

from django.conf import settings
from subprocess import check_call

SASS_INCLUDE_PATHS = [
    os.path.join(PROJECT_DIR, "gems", "chunky_png"),
    os.path.join(PROJECT_DIR, "gems", "compass"),
    os.path.join(PROJECT_DIR, "gems", "rubygems"),
]

class SCSS(Compiler):
    def compiler(self, inputs):
        for filename in inputs:
            command = [ "sass", "-C", "-t", "expanded" ]

            for path in SASS_INCLUDE_PATHS:
                command.append("-I")
                command.append('"path"')

            if settings.DEBUG:
                command.append("--line-numbers")

            check_call(command)

