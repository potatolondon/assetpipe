import os
from setuptools import setup, find_packages

NAME = 'assetpipe'
PACKAGES = find_packages()
DESCRIPTION = 'Static asset management for Django'
URL = "https://github.com/potatolondon/assetpipe"
LONG_DESCRIPTION = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()
AUTHOR = 'Potato London Ltd.'

EXTRAS = {}

setup(
    name=NAME,
    version='0.8.0',
    packages=PACKAGES,
    # metadata for upload to PyPI
    author=AUTHOR,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    keywords=["assetpipe", "Django", "Google App Engine"],
    url=URL,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    # dependencies
    extras_require=EXTRAS,
)
