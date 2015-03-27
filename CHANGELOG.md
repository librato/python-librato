## Changelog

### Version 0.8.2
* New method to retrieve all metrics with pagination. Thanks @Bachmann1234.

### Version 0.8.1
* Return `rearm_seconds` and `active` properties for alerts

### Version 0.8.0
* Release support for Alerts

### Version 0.7.0
* Release 0.7.0: allow "composite" to be specified when adding a new Stream to an Instrument.  Also allow a new Instrument object to be saved directly.

### Version 0.6.0
* New release: client-side aggregation support

### Version 0.5.1
* Tweak behavior of optional metric name sanitizer; pypy support

### Version 0.5.0
* Release 0.5.0 - adds the option to sanitize metric names; other minor changes

### Version 0.4.14
* Fix issues in Gauge#add and Counter#add per #69

### Version 0.4.13
* Update setup.py to include supported Python versions

### Version 0.4.12
* Releasing new version. Auto submit in queue.

### Version 0.4.11
* Preliminary support for Annotations (retrieve only).

### Version 0.4.10
* Separate deleting a single metric from deleting a batch of metrics.
  Thanks @Bachmann1234.

### Version 0.4.9
* Adding dashboard and instrument support. Thanks @sargun.

### Version 0.4.8
* More explicit exception if user provides non-ascii data for the credentials.

### Version 0.4.5
* Same as 0.4.4. Just making sure there are no distribution issues after
  changing the Hosting Mode in pypi.

### Version 0.4.4
* Consolidates parameter name in queue. Thanks to @stevepeak to point this out.

### Version 0.4.3
* Adding support to update metric attributes

### Version 0.4.2
* Fixing reading the charset of a response in python2.

### Version 0.4.1
* python3 support thanks to @jacobian fantastic work.

### Version 0.2.7
* Update User-Agent string to follow standards.

### Version 0.2.6
* Refactoring _mexe().
* Setting User-Agent header.

### Version 0.2.5
* Fixing authorship in pypi.

### Version 0.2.4
* Fixing packaging issues.

### Version 0.2.3
* New library entry points to reflect latest API endpoints.

### Version 0.2.2
* Support for sending measurements in batch mode.

### Version 0.2.1
* Unit Testing infrastructure.
* Mocking librato API.
* Improve integration tests.

### Version 0.2.0
* Initial release.
* Chris Moyer's (AKA @kopertop) code moved from bitbucket to github.
