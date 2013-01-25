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

Let's now create a Metric:

```
  api.submit("temperature", 10, description="temperature at home")
```

By default ```submit()``` will create a gauge metric. The metric will be
created automatically by the server if it does not exist. We can remove that
metric with:

```
  api.delete("temperature")
```

For creating a counter metric, we can:

```
  api.submit("connections", 20, type='counter', description="server connections")
```

And again to remove:

```
  api.delete("connections")
```

To iterate over your metrics:

```
  for m in api.list_metrics():
    print "%s: %s" % (m.name, m.description)
```

To retrieve a specific metric use ```get()```:

```
  gauge   = api.get("temperature")
  counter = api.get("connections")
```

For sending more measurements:

```
  for temp in [20, 21, 22]:
    api.submit('temperature', temp)
  for num_con in [100, 200, 300]:
    api.submit('connections', num_con, type='counter')
```

Let's now iterate over the measurements of our Metrics:

```
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
in batch mode. We push measurements that are saved in memory and when we are
ready, they will be submitted in an efficient matter. Here is an example:

```
api = librato.connect(user, token)
q   = api.new_queue()
q.add('temperature', 22.1, source='upstairs')
q.add('temperature', 23.1, source='dowstairs')
q.add('num_requests', 100, type='counter', source='server1')
q.add('num_requests', 102, type='counter', source='server2')
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
