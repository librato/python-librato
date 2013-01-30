#!/usr/bin/python
#
# python setup.py sdist upload

try:
  from setuptools import setup, find_packages
except ImportError:
  from ez_setup import use_setuptools
  use_setuptools()
  from setuptools import setup, find_packages

from librato import __version__

setup(
  name = "librato-metrics",
  version = __version__,
  description = "Python API Wrapper for Librato",
  long_description="Python Wrapper for the Librato Metrics API: http://dev.librato.com/v1/metrics",
  author = "Librato",
  author_email = "support@librato.com",
  url = 'http://github.com/librato/python-librato',
  license = 'https://github.com/librato/python-librato/blob/master/LICENSE',
  packages= ['librato'],
  package_data={'': ['LICENSE', 'README.md', 'CHANGELOG.md']},
  package_dir={'librato': 'librato'},
  include_package_data=True,
  platforms = 'Posix; MacOS X; Windows',
  classifiers = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Topic :: Internet',
  ],
  dependency_links = [],
  install_requires = [],
)
