#!/usr/bin/env python
from setuptools import setup, find_packages

setup(name="python-librato",
      version="0.0.1",
      description = "Python API Wrapper for Librato",
      long_description="Python Wrapper for the Librato Metrics API: http://dev.librato.com/v1/metrics",
      license="MIT??",
      install_requires=['requests'],
      author="XXXXXXXXXXXXX",
      author_email="XXXXXXXXXXXXXXXXXX"
      url = "http://dev.librato.com/v1/metrics",
      packages = find_packages(),
      keywords= "librato",
      zip_safe = True)
