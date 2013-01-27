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

setup(name = "librato-metrics",
		version = __version__,
		description = "Python API Wrapper for Librato",
		long_description="Python Wrapper for the Librato Metrics API: http://dev.librato.com/v1/metrics",
		author = "Joseph Ruscio",
		author_email = "joe@librato.com",
    maintainer = "David Rio-Deiros",
    maintainer_email = "driodeiros@gmail.com",
		url = "http://dev.librato.com/v1/metrics",
		packages = ['librato'],
		include_package_data = True,
    package_data = { '': ['LICENSE', 'README.md', 'CHANGELOG.md'] },
		license = 'LICENSE',
		scripts = [],
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
