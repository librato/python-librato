python-librato
==============

[![Build Status](https://secure.travis-ci.org/librato/python-librato.png?branch=master)](http://travis-ci.org/librato/python-librato)

A Python wrapper for the Librato Metrics API.

## Installation

In your shell:

  ```$ easy_install librato-metrics```

  or

  ```$ pip install librato-metrics```

From your application or script:

  ```import  librato```

## Authenticating

  We first use our credentials to connect to the API. I am assuming you have
[a librato account for Metrics](https://metrics.librato.com/). Go to your
[account settings page](https://metrics.librato.com/account) and save your
username (email address) and token (long hexadecimal string).

```python
  api = librato.connect(user, token)
```

## Basic Usage

To iterate over your metrics:

```python
  for m in api.list_metrics():
    print m.name
```

Let's now create a Metric:

```python
  api.submit("temperature", 10, description="temperature at home")
```

By default ```submit()``` will create a gauge metric. The metric will be
created automatically by the server if it does not exist. We can remove it:

```python
  api.delete("temperature")
```

For creating a counter metric, we can:

```python
  api.submit("connections", 20, type='counter', description="server connections")
```

And again to remove:

```python
  api.delete("connections")
```

To iterate over your metrics:

```python
  for m in api.list_metrics():
    print "%s: %s" % (m.name, m.description)
```

To retrieve a specific metric:

```python
  gauge   = api.get("temperature")
  counter = api.get("connections")
```

For sending more measurements:

```python
  for temp in [20, 21, 22]:
    api.submit('temperature', temp)
  for num_con in [100, 200, 300]:
    api.submit('connections', num_con, type='counter')
```

Let's now iterate over the measurements of our Metrics:

```python
  metric = api.get("temperature", count=100, resolution=1)
  for m in metric.measurements['unassigned']:
    print "%s: %s" % (m['value'], m['measure_time'])
```

Notice a couple of things here. First, we are using the key `unassigned` since
we have not associated our measurements to any source. Read more about it in
the [API documentation](http://dev.librato.com/v1). In addition, notice how
we are passing the count and resolution parameters to make sure the API
returns measurements in its answer and not only the metric properties.
Read more about them [here](http://dev.librato.com/v1/time-intervals).

## Sending measurements in batch mode

Sending a measurement in a single HTTP request is inefficient. The overhead
both at protocol and backend level is very high. That's why we provide an
alternative method to submit your measurements. The idea is to send measurements
in batch mode. We push measurements that are stored and when we are
ready, they will be submitted in an efficient matter. Here is an example:

```python
api = librato.connect(user, token)
q   = api.new_queue()
q.add('temperature', 22.1, source='upstairs')
q.add('temperature', 23.1, source='dowstairs')
q.add('num_requests', 100, type='counter', source='server1')
q.add('num_requests', 102, type='counter', source='server2')
q.submit()
```

## Updating Metrics

You can update the information for a metric by using the `update` method,
for example:

```python
api = librato.connect(user, token)
for metric in api.list_metrics():
  gauge = api.get(m.name)
  attrs = gauge.attributes
  attrs['display_units_long'] = 'ms'
  api.update(metric.name, attributes=attrs)
```

## Annotations

List Annotation all annotation streams:

```python
for stream in api.list_annotation_streams
print "%s:%s" % (stream.name,stream.display_name)
```

View the metadata on a named annotation stream:

```python
stream=api.get_annotation_stream("api.pushes")
print stream
```

Retrieve all of the events inside a named annotation stream, by adding a
start_time parameter to the get_annotation_stream() call:

```python
stream=api.get_annotation_stream("api.pushes",start_time="1386050400")
for source in stream.events:
	print source
	events=stream.events[source]
	for event in events:
		print event['id']
		print event['title']
		print event['description']
```

Submit a new annotation to a named annotation stream (creates the stream if it
doesn't exist). Title is a required parameter, and all other parameters are optional

```python
api.post_annotation("testing",title="foobarbiz")

api.post_annotation("TravisCI",title="build %s"%travisBuildID, source=SystemSource, description="Application %s, Travis build %s"%(appName,travisBuildID))
```

Delete a named annotation stream:

```python
api.delete_annotation_stream("testing")
```

## Contribution

Do you want to contribute? Do you need a new feature? Please open a
[ticket](https://github.com/librato/python-librato/issues).

## Contributors

The original version of `python-librato` was conceived/authored/released by Chris Moyer (AKA [@kopertop](https://github.com/kopertop)). He's
graciously handed over maintainership of the project to us and we're super-appreciative of his efforts.

## Copyright

Copyright (c) 2011-2014 [Librato Inc.](http://librato.com) See LICENSE for details.
