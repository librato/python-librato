## Changelog

### Version 3.1.0
Added the ability to inherit tags
Readme updates for tag usage
Added ability to use envvars when creating a connection
Added generators for pagination

### Version 3.0.1
* Submit in tag mode if default tags present in queue

### Version 3.0.0
* (!) Deprecated Dashboards and Instruments in favor of Spaces and Charts
* Allow custom user agent
* Minor bug fixes

### Version 2.1.2
* Allow hash argument when querying tagged data

### Version 2.1.1
* Allow creation of Tagged spaces

### Version 2.1.0
* Transparent Multidimensional support.

### Version 2.0.1
* Fix Alert issues in #142

### Version 2.0.0
* Multi Dimension support
* pep8 compliant
* All that thanks to @vaidy4github great work

### Version 1.0.7
* Better response handling (Thanks @jhaegg).

### Version 1.0.6
* Better param encoding

### Version 1.0.5
* Add new property for streams

### Version 1.0.4
* Fix issue loading streams with gap_detection set; fix 403 error parsing

### Version 1.0.3
* Adds missing property in streams

### Version 1.0.2
* Added support for for Service attributes

### Version 1.0.1
* Stream model supports all stream properties

### Version 1.0.0
* Spaces API support

### Version 0.8.6
* Allow http for local dev (thanks @vaidy4github)

### Version 0.8.5
* Same as 0.8.4. Resubmitting to pypi.

### Version 0.8.4
* Add timeout support.
* Various Bug fixes. Thanks @marcelocure

### Version 0.8.3
* Persisting composite metrics.

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
