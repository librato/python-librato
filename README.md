python-librato
==============

[![Build Status](https://secure.travis-ci.org/librato/python-librato.png?branch=master)](http://travis-ci.org/librato/python-librato)

A Python wrapper for the Librato Metrics API.

## Sections

## Installation

In your shell:

  ```$ easy_install librato-metrics```

  or

  ```$ pip install librato-metrics```

From your application or script:

  ```import librato```

## Authentication

  We first use our credentials to connect to the API. I am assuming you have
[a librato account for Metrics](https://metrics.librato.com/). Go to your
[account settings page](https://metrics.librato.com/account) and save your
username (email address) and token (long hexadecimal string).

```python
  api = librato.connect('email', 'token')
```

When creating your connection you may choose to provide a sanitization function.
This will be applied to any metric name you pass in. For example we provide a
sanitization function that will ensure your metrics are legal librato names.
This can be set as such

```python
  api = librato.connect('email', 'token', sanitizer=librato.sanitize_metric_name)
```

By default no sanitization is done.

## Basic Usage

To iterate over your metrics:

```python
  for m in api.list_metrics():
    print m.name
```

or use `list_metrics()` to iterate over all your metrics with
transparent pagination.

Let's now create a Metric:

```python
    api.submit("temperature", 10, tags={'city': 'Barcelona'})
```

The metric will be created automatically by the server if it does not exist.

To iterate over your metric names:

```python
    for m in api.list_metrics():
        print "%s: %s" % (m.name, m.description)
```

To retrieve a specific metric:

```python
    tags = {"city": "Barcelona}
    metric = api.get_metric("temperature")
    metric.name # "temperature"

    # Retrieve the last measurements seen on that metric
    data = api.get("temperature", duration=60, tags=tags)
    data = self.api.get(name, duration=60, tags=tags)
    data['series'][0]['measurements']
```

Iterate over measurements:

```python
    data = api.get("temperature", duration=60, tags=tags)
    data = self.api.get(name, duration=60, tags=tags)
    data['series'][0]['measurements']
    for m in data['series'][0]['measurements']:
        print m
```

To retrieve a composite metric:

```python
	compose = 'mean(s("' + name + '", "*", {function: "mean", period: "3600"}))'
	import time
	start_time = int(time.time()) - 3600
	data = self.api.get_composite(compose, start_time=start_time)
	for m in data['series'][0]['measurements']:
		print m
```

To create a saved composite metric:

```python
  api.create_composite('humidity', 'sum(s("all.*", "*"))', description='a test composite')
```

Delete a metric:

```python
  api.delete("temperature")
```

## Sending measurements in batch mode

Sending a measurement in a single HTTP request is inefficient. The overhead
both at protocol and backend level is very high. That's why we provide an
alternative method to submit your measurements. The idea is to send measurements
in batch mode. We push measurements that are stored and when we are
ready, they will be submitted in an efficient manner. Here is an example:

```python
    q = api.new_queue()
    q.add('temperature', 12, tags={'city': 'sf'      , 'station': '12'})
    q.add('temperature', 14, tags={'city': 'new york', 'station': '1'})
    q.add('temperature', 22, tags={'city': 'austin'  , 'station': '112'})
    q.submit()
```

Queues can also be used as context managers. Once the context block is complete the queue
is submitted automatically. This is true even if an exception interrupts flow. In the
example below if ```potentially_dangerous_operation``` causes an exception the queue will
submit the first measurement as it was the only one successfully added.
If the operation succeeds both measurements will be submitted.

```python
api = librato.connect('email', 'token')
with api.new_queue() as q:
    q.add('temperature', 22.1, tags={'city': 'sf', 'station': '12'})
    potentially_dangerous_operation()
    q.add('num_requests', tags={'city': 'austin', 'station': '112'})
```

Queues by default will collect metrics until they are told to submit. You may create a queue
that autosubmits based on metric volume.

```python
	api = librato.connect('email', 'token')
	# Submit when the 400th metric is queued
	q = api.new_queue(auto_submit_count=400)
```

## Updating Metric Attributes

You can update the information for a metric by using the `update` method,
for example:

```python
	metric = self.api.get_metric("temperature")
	attrs = metric.attributes
	attrs['description'] = "A temperature metric"
	self.api.update(name, attributes=attrs)
```

## Annotations

List Annotation all annotation streams:

```python
for stream in api.list_annotation_streams():
print("%s: %s" % (stream.name, stream.display_name))
```

View the metadata on a named annotation stream:

```python
stream = api.get_annotation_stream("api.pushes")
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

api.post_annotation("TravisCI",title="build %s"%travisBuildID,
                     source="SystemSource",
                     description="Application %s, Travis build %s"%(appName,travisBuildID),
                     links=[{'rel': 'travis', 'href': 'http://travisci.com/somebuild'}])
```

Delete a named annotation stream:

```python
api.delete_annotation_stream("testing")
```

## Alerts

List all alerts:

```python
for alert in api.list_alerts():
    print(alert.name)
```

Create an alert with an _above_ condition:
```python
alert = api.create_alert('my.alert')
alert.add_condition_for('metric_name').above(1) # trigger immediately
alert.add_condition_for('metric_name').above(1).duration(60) # trigger after a set duration
alert.add_condition_for('metric_name').above(1, 'sum') # custom summary function
alert.save()
```

Create an alert with a _below_ condition:
```python
alert = api.create_alert('my.alert', description='An alert description')
alert.add_condition_for('metric_name').below(1) # the same syntax as above conditions
alert.save()
```

Create an alert with an _absent_ condition:
```python
alert = api.create_alert('my.alert')
alert.add_condition_for('metric_name').stops_reporting_for(5) # duration in minutes of the threshold to trigger the alert
alert.save()
```

Restrict the condition to a specific source (default is `*`):
```python
alert = api.create_alert('my.alert')
alert.add_condition_for('metric_name', 'mysource')
alert.save()
```

View all outbound services for the current user
```python
for service in api.list_services():
    print(service._id, service.title, service.settings)
```

Create an alert with Service IDs
```python
alert = api.create_alert('my.alert', services=[1234, 5678])
```

Create an alert with Service objects
```python
s = api.list_services()
alert = api.create_alert('my.alert', services=[s[0], s[1]])
```

Add an outbound service to an alert:
```python
alert = api.create_alert('my.alert')
alert.add_service(1234)
alert.save()
```

Put it all together:
```python
cond = {'metric_name': 'cpu', 'type': 'above', 'threshold': 42}
s = api.list_services()
api.create_alert('my.alert', conditions=[cond], services=[s[0], s[1]])
# We have an issue at the API where conditions and services are not returned
# when creating. So, retrieve back from API
alert = api.get_alert('my.alert')
print(alert.conditions)
print(alert.services)
```


## Client-side Aggregation

You can aggregate measurements before submission using the `Aggregator` class.  Optionally, specify a `measure_time` to submit that timestamp to the API.  You may also optionally specify a `period` to floor the timestamp to a particular interval.  If `period` is specified without a `measure_time`, the current timestamp will be used, and floored to `period`.  Specifying an optional `source` allows the aggregated measurement to report a source name.

Aggregator instances can be sent immediately by calling `submit()` or added to a `Queue` by calling `queue.add_aggregator()`.

```python
from librato.aggregator import Aggregator

api = librato.connect('email', 'token')

a = Aggregator(api)
a.add("foo", 42)
a.add("foo", 5)
# count=2, min=5, max=42, sum=47 (value calculated by API = mean = 23.5), source=unassigned
# measure_time = <now>
a.submit()

a = Aggregator(api, source='my.source', period=60)
a.add("foo", 42)
a.add("foo", 5)
# count=2, min=5, max=42, sum=47 (value calculated by API = mean = 23.5), source=my.source
# measure_time = <now> - (<now> % 60)
a.submit()

a = Aggregator(api, period=60, measure_time=1419302671)
a.add("foo", 42)
a.add("foo", 5)
# count=2, min=5, max=42, sum=47 (value calculated by API = mean = 23.5), source=unassigned
# measure_time = 1419302671 - (1419302671 % 60) = 1419302671 - 31 = 1419302640
a.submit()

a = Aggregator(api, measure_time=1419302671)
a.add("foo", 42)
a.add("foo", 5)
# count=2, min=5, max=42, sum=47 (value calculated by API = mean = 23.5), source=unassigned
# measure_time = 1419302671
a.submit()


# You can also add an Aggregator instance to a queue
q = librato.queue.Queue(api)
q.add_aggregator(a)
q.submit()
```

## Misc

### Timeouts

Timeouts are provided by the underlying http client. By default we timeout at 10 seconds. You can change
that by using `api.set_timeout(timeout)`.

## Contribution

Do you want to contribute? Do you need a new feature? Please open a
[ticket](https://github.com/librato/python-librato/issues).

## Contributors

The original version of `python-librato` was conceived/authored/released by Chris Moyer (AKA [@kopertop](https://github.com/kopertop)). He's
graciously handed over maintainership of the project to us and we're super-appreciative of his efforts.

## Copyright

Copyright (c) 2011-2016 [Librato Inc.](http://librato.com) See LICENSE for details.
