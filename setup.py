#!/usr/bin/python
#
import os
import sys
from setuptools import setup

if sys.argv[-1] == 'publish':
  os.system('python setup.py sdist upload')
  sys.exit()

setup(
  name = "librato-metrics",
  version = "0.8.5", # Update also in __init__ ; look into zest.releaser to avoid having two versions
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
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
  ],
  dependency_links = [],
  install_requires = ['six'],
)
