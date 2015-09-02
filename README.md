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

When creating your connection you may choose to provide a sanitization function.
This will be applied to any metric name you pass in. For example we provide a
sanitization function that will ensure your metrics are legal librato names.
This can be set as such

```python
  api = librato.connect(user, token, sanitizer=librato.sanitize_metric_name)
```

By default no sanitization is done.

## Basic Usage

To iterate over your metrics:

```python
  for m in api.list_metrics():
    print m.name
```

or use `list_all_metrics()` to iterate over all your metrics with
transparent pagination.

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

To retrieve a composite metric:

```python
  # Get average temperature in all cities for last 8 hours
  compose = 'mean(s("temperature", "*", {function: "mean", period: "3600"}))'
  start_time = int(time.time()) - 8 * 3600
  resp = api.get_composite(compose, start_time=start_time)
  resp['measurements'][0]['series']
  # [
  #   {u'measure_time': 1421744400, u'value': 41.23944444444444},
  #   {u'measure_time': 1421748000, u'value': 40.07611111111111},
  #   {u'measure_time': 1421751600, u'value': 38.77444444444445},
  #   {u'measure_time': 1421755200, u'value': 38.05833333333333},
  #   {u'measure_time': 1421758800, u'value': 37.983333333333334},
  #   {u'measure_time': 1421762400, u'value': 38.93333333333333},
  #   {u'measure_time': 1421766000, u'value': 40.556666666666665}
  # ]
```

For sending more measurements:

```python
  for temp in [20, 21, 22]:
    api.submit('temperature', temp)
  for num_con in [100, 200, 300]:
    api.submit('connections', num_con, type='counter')
```

To create a composite metric:

```python
  api.create_composite('humidity', 'sum(s("all.*", "*"))', description="a test composite")
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
ready, they will be submitted in an efficient manner. Here is an example:

```python
api = librato.connect(user, token)
q   = api.new_queue()
q.add('temperature', 22.1, source='upstairs')
q.add('temperature', 23.1, source='dowstairs')
q.add('num_requests', 100, type='counter', source='server1')
q.add('num_requests', 102, type='counter', source='server2')
q.submit()
```

Queues can also be used as context managers. Once the context block is complete the queue
is submitted automatically. This is true even if an exception interrupts flow. In the
example below if ```potentially_dangerous_operation``` causes an exception the queue will
submit the first measurement as it was the only one successfully added.
If the operation succeeds both measurements will be submitted.

```python
api = librato.connect(user, token)
with api.new_queue() as q:
    q.add('temperature', 22.1, source='upstairs')
    potentially_dangerous_operation()
    q.add('num_requests', 100, type='counter', source='server1')
```

Queues by default will collect metrics until they are told to submit. You may create a queue
that autosubmits based on metric volume.

```python
api = librato.connect(user, token)
# Submit when the 400th metric is queued
q = api.new_queue(auto_submit_count=400)
```

## Client-side Aggregation

You can aggregate measurements before submission using the `Aggregator` class.  Optionally, specify a `measure_time` to submit that timestamp to the API.  You may also optionally specify a `period` to floor the timestamp to a particular interval.  If `period` is specified without a `measure_time`, the current timestamp will be used, and floored to `period`.  Specifying an optional `source` allows the aggregated measurement to report a source name.

Aggregator instances can be sent immediately by calling `submit()` or added to a `Queue` by calling `queue.add_aggregator()`.

```python
from librato.aggregator import Aggregator

api = librato.connect(email, token)

a = Aggregator(api)
a.add("foo", 42)
a.add("bar", 5)
# count=2, min=5, max=42, sum=47 (value calculated by API = mean = 23.5), source=unassigned
a.submit()

a = Aggregator(api, source='my.source', period=60)
a.add("foo", 42)
a.add("bar", 5)
# count=2, min=5, max=42, sum=47 (value calculated by API = mean = 23.5), source=my.source
# measure_time = <now> - (<now> % 60)
a.submit()

a = Aggregator(api, period=60, measure_time=1419302671)
a.add("foo", 42)
a.add("bar", 5)
# count=2, min=5, max=42, sum=47 (value calculated by API = mean = 23.5), source=unassigned
# measure_time = <now> - (<now> % 60) = 1419302640
a.submit()

a = Aggregator(api, measure_time=1419302671)
a.add("foo", 42)
a.add("bar", 5)
# count=2, min=5, max=42, sum=47 (value calculated by API = mean = 23.5), source=unassigned
# measure_time = 1419302671
a.submit()


# You can also add an Aggregator instance to a queue
q = librato.queue.Queue(api)
q.add_aggregator(a)
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

api.post_annotation("TravisCI",title="build %s"%travisBuildID,
                     source=SystemSource,
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
    print alert.name
```

Create alerts with an _above_ condition:
```python
alert = api.create_alert(name)
alert.add_condition_for('metric_name').above(1) # immediately
alert.add_condition_for('metric_name').above(1).duration(60) # duration of the threshold to trigger the alert
alert.add_condition_for('metric_name').above(1, 'sum') # custom summary function
alert.save()
```

Create alerts with a _below_ condition:
```python
api.create_alert(name)
alert.add_condition_for('metric_name').below(1) # the same syntax from above conditions
alert.save()
```

Create alerts with an _absent_ condition:
```python
api.create_alert(name)
alert.add_condition_for('metric_name').stops_reporting_for(1) # duration of the threshold to trigger the alert
alert.save()
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

Thanks also to [@Bachmann1234](https://github.com/Bachmann1234) for continually improving this library.

## Copyright

Copyright (c) 2011-2014 [Librato Inc.](http://librato.com) See LICENSE for details.
