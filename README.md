python-librato
==============

[![Build Status](https://secure.travis-ci.org/librato/python-librato.png?branch=master)](http://travis-ci.org/librato/python-librato)

A Python wrapper for the Librato Metrics API.

## Documentation Notes

- New accounts
  - Refer to [master](https://github.com/librato/python-librato/tree/master) for the latest documentation.
- Legacy (source-based) Librato users
  - Please see the [legacy documentation](https://github.com/librato/python-librato/tree/v2.1.2)

## Installation

In your shell:

  ```$ easy_install librato-metrics```

  or

  ```$ pip install librato-metrics```

From your application or script:

  ```import librato```

## Authentication

Assuming you have
[a Librato account](https://metrics.librato.com/), go to your
[account settings page](https://metrics.librato.com/account) and get your
username (email address) and token (long hexadecimal string).

```python
  api = librato.connect('email', 'token')
```

### Metric name sanitization

When creating your connection you may choose to provide a sanitization function.
This will be applied to any metric name you pass in. For example we provide a
sanitization function that will ensure your metrics are legal librato names.
This can be set as such:

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

or use `list_all_metrics()` to iterate over all your metrics with
transparent pagination.

Let's now create a metric:

```python
  api.submit("temperature", 80, tags={"city": "sf"})
```

View your metric names:

```python
  for m in api.list_metrics():
      print(m.name)
```

To retrieve a metric:

```python
  # Retrieve metric metadata ONLY
  gauge = api.get("temperature")
  gauge.name # "temperature"

  # Retrieve measurements from last 15 minutes
  resp = api.get_measurements("temperature", duration=900, resolution=1)
  # {u'name': u'temperature',
  # u'links': [],
  # u'series': [{u'measurements': [
  #   {u'value': 80.0, u'time': 1502917147}
  # ],
  # u'tags': {u'city': u'sf'}}],
  # u'attributes': {u'created_by_ua': u'python-librato/2.0.0...'
  # , u'aggregate': False}, u'resolution': 1}
```

To retrieve a composite metric:

```python
  # Get average temperature across all cities for last 8 hours
  compose = 'mean(s("temperature", "*", {function: "mean", period: "3600"}))'
  import time
  start_time = int(time.time()) - 8 * 3600

  # For tag-based (new) accounts.
  # Will be deprecated in favor of `get_composite` in a future tags-only release
  resp = api.get_composite_tagged(compose, start_time=start_time)
  resp['series']
  # [
  #   {
  #     u'query': {u'metric': u'temperature', u'tags': {}},
  #     u'metric': {u'attributes': {u'created_by_ua': u'statsd-librato-backend/0.1.7'},
  #     u'type': u'gauge',
  #     u'name': u'temperature'},
  #     u'measurements': [{u'value': 42.0, u'time': 1504719992}],
  #     u'tags': {u'one': u'1'}}],
  #     u'compose': u's("foo", "*")',
  #     u'resolution': 1
  #   }
  # ]

  # For backward compatibility in legacy Librato (source-based)
  resp = api.get_composite(compose, start_time=start_time)
```

To create a saved composite metric:

```python
  api.create_composite('composite.humidity', 'sum(s("humidity", "*"))',
      description='a test composite')
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
api = librato.connect('email', 'token')
q = api.new_queue()
q.add('temperature', 22.1, tags={'location': 'downstairs'})
q.add('temperature', 23.1, tags={'location': 'upstairs'})
q.submit()
```

Queues can also be used as context managers. Once the context block is complete the queue
is submitted automatically. This is true even if an exception interrupts flow. In the
example below if ```potentially_dangerous_operation``` causes an exception the queue will
submit the first measurement as it was the only one successfully added.
If the operation succeeds both measurements will be submitted.

```python
with api.new_queue() as q:
    q.add('temperature', 22.1, tags={'location': 'downstairs'})
    potentially_dangerous_operation()
    q.add('num_requests', 100, tags={'host': 'server1')
```

Queues by default will collect metrics until they are told to submit. You may create a queue
that autosubmits based on metric volume.


```python
# Submit when the 400th metric is queued
q = api.new_queue(auto_submit_count=400)
```

## Tag Inheritance

Tags can be inherited from the queue or connection object if `inherit_tags=True` is passed as
an attribute.  If inherit_tags is not passed, but tags are added to the measurement, the measurement
tags will be the only tags added to that measurement.  

When there are tag collisions, the measurement, then the batch, then the connection is the order of
priority.

```python
api = librato.connect('email', 'token', tags={'company': 'librato', 'service': 'app'})

# tags will be {'city': 'sf'}
api.submit('temperature', 80, tags={'city': 'sf'})

# tags will be {'city': 'sf', 'company': 'librato', 'service': 'app'}
api.submit('temperature', 80, tags={'city': 'sf'}, inherit_tags=True)

q = api.new_queue(tags={'service':'api'})

# tags will be {'location': 'downstairs'} 
q.add('temperature', 22.1, tags={'location': 'downstairs'})

# tags will be {'company': 'librato', 'service':'api'}
q.add('temperature', 23.1)

# tags will be {'location': 'downstairs', 'company': 'librato', 'service': 'api'}
q.add('temperature', 22.1, tags={'location': 'downstairs'}, inherit_tags=True)
q.submit()
```

## Updating Metric Attributes

You can update the information for a metric by using the `update` method,
for example:

```python
for metric in api.list_metrics(name="abc*"):
  attrs = metric.attributes
  attrs['display_units_short'] = 'ms'
  api.update(metric.name, attributes=attrs)
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

## Spaces API
### List Spaces
```python
# List spaces
spaces = api.list_spaces()
```

### Create a Space
```python
# Create a new Space directly via API
space = api.create_space("space_name")
print("Created '%s'" % space.name)

# Create a new Space via the model, passing the connection
space = Space(api, 'Production')
space.save()
```

### Find a Space
```python
space = api.find_space('Production')
```

### Delete a Space
```python
space = api.create_space('Test')
api.delete_space(space.id)
# or
space.delete()
```

### Create a Chart

```python
# Create a line chart with various metric streams including their tags(s) and group/summary functions:
space = api.get_space(123)
linechart = api.create_chart(
  'cities MD line chart',
  space,
  streams=[
    {
      "metric": "librato.cpu.percent.idle",
      "tags": [{"name": "environment", "values": ["*"]]
    },
    {
      "metric": "librato.cpu.percent.user",
      "tags": [{"name": "environment", 'dynamic': True}]
    }
  ]
)
```

### Find a Chart
```python
# Takes either space_id or a space object
chart = api.get_chart(chart_id, space_id)
chart = api.get_chart(chart_id, space)
```

### Update a Chart

```python
space = api.get_space(123)
charts = space.chart_ids
chart = api.get_chart(charts[0], space.id)
chart.name = 'Your chart name'
chart.save()
```

### Rename a Chart
```python
chart = api.get_chart(chart_id, space_id)
# save() gets called automatically here
chart.rename('new chart name')
```

### Delete a Chart
```python
chart = api.get_chart(chart_id, space_id)
chart.delete()
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

## Misc

### Timeouts

Timeouts are provided by the underlying http client. By default we timeout at 10 seconds. You can change
that by using `api.set_timeout(timeout)`.

## Contribution

Want to contribute? Need a new feature? Please open an
[issue](https://github.com/librato/python-librato/issues).

## Contributors

The original version of `python-librato` was conceived/authored/released by Chris Moyer (AKA [@kopertop](https://github.com/kopertop)). He's
graciously handed over maintainership of the project to us and we're super-appreciative of his efforts.

## Copyright

Copyright (c) 2011-2017 [Librato Inc.](http://librato.com) See LICENSE for details.
