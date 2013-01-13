python-librato
==============

[![Build Status](https://magnum.travis-ci.com/librato/python-librato.png?token=5DkaEcPsGmzNFtrdssjk)](http://magnum.travis-ci.com/librato/python-librato)

A Python wrapper for the Librato Metrics API.

## Installation

In your shell:

  ```$ easy_install librato-python```

  or

  ```$ pip install librato-python```

From your application or script:

  ```import  librato```

## Authenticating

  The first thing we to is preseting the credentials so we have access to the
  metrics api. I am assuming you have
  [a librato account for Metrics](https://metrics.librato.com/). Go to your
  [account settings page](https://metrics.librato.com/account)
  and save your username and token.

```
  api = librato.connect(user, token)
```

## Basic Usage

To iterate over your metrics:

```
  for m in api.list_metrics():
    print m.name
```

Let's now create a Gauge Metric:

```
  gauge = api.create_gauge("temperature", description="temperature at home")
```

And we can remove using:

```
  api.delete_gauge("temperature")
```

And for counter metrics:

```
  counter = api.create_counter("connections", description="server connections")
  api.delete_counter("connections")
```

To iterate over your metrics:

```
  for m in api.list_metrics():
    print "%s: %s" % (m.name, m.description)
```

To retrieve a concrete gauge or counter:

```
  gauge   = api.get_gauge("temperature")
  counter = api.get_counter("connections")
```

Now, let's send some data to our metrics:

```
  for temp in [20, 21, 22]:
    api.send_gauge_value('temperature', temp)
```

and for our connections (a counter metric):

```
  for num_con in [100, 200, 300]:
    api.send_counter_value('connections', num_con)
```

Let's now iterate over the measurements of our Metrics:

```
  measurements = api.get_gauge("temperature", resolution=1, count=10).measurements
  for m in measurements['unassigned']:
    print "%s: %s" % (m['value'], m['measure_time'])
```

```
  measurements = api.get_counter("connections", resolution=1, count=10).measurements
  for m in measurements['unassigned']:
    print "%s: %s" % (m['value'], m['measure_time'])
```

Notice how we are using the key `unassigned` since we have not associated our
measurements to any source. Read more about it in the
[API documentation](http://dev.librato.com/v1).

## Sending measurements in batching mode

Sending a measurement in a single HTTP request is inefficient. The overhead
both at protocol and backend level is very high. That's why we provide an
alternative method to submit your measurements. The idea is to send measurements
in batch mode. We push measurements that are saved in memory and when we are
ready, they will be submitted in an efficient matter. Let me show you:

```
api = librato.connect(user, token)
q   = api.new_queue()
q.push('temperature', 22.1, source='upstairs')
q.push('temperature', 23.1, source='dowstairs')
q.push('num_requests', 100, type='counter', source='server1')
q.push('num_requests', 102, type='counter', source='server2')
q.submit()
```

## Contribution

Do you want to contribute? Do you need a new feature? Please open a
[ticket](https://github.com/librato/python-librato/issues).

## Contributors

The original version of `python-librato` was conceived/authored/released by Chris Moyer (AKA [@kopertop](https://github.com/kopertop)). He's
graciously handed over maintainership of the project to us and we're super-appreciative of his efforts.

## Copyright

Copyright (c) 2011-2013 [Librato Inc.](http://librato.com) See LICENSE for details.
