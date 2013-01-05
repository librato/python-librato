# Copyright (c) 2012 Chris Moyer http://coredumped.org
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

class Metric(object):
  """Librato Metric Base class"""

  def __init__(self, connection, name, attributes=None, period=None, description=None):
    self.connection = connection
    self.name = name
    self.attributes=attributes or {}
    self.period = period
    self.description = description
    self.measurements = {}

  def __getitem__(self, name):
    return self.attributes[name]

  def get(self, name, default=None):
    return self.attributes.get(name, default)

  @classmethod
  def from_dict(cls, connection, data):
    """Returns a metric object from a dictionary item,
    which is usually from librato's API"""
    if data.get('type') == "gauge":
      cls = Gauge
    elif data.get('type') == "counter":
      cls = Counter

    obj = cls(connection, data['name'])
    obj.period = data['period']
    obj.attributes = data['attributes']
    obj.description = data['description']
    obj.measurements = data['measurements'] if data.has_key('measurements') else {}

    return obj

  def push(self, value, source=None, **params):
    """Store a measurement for sending later"""
    if not params:
      params = {}
    params["value"] = value
    if source:
      params["source"] = source
    params["name"] = self.name
    self.measurements[self.what_am_i()].append(params)

  def submit(self):
    """submit all the measurements available"""
    r = self.connection._submit_batch_measurements(self.measurements)
    self.measurements[self.what_am_i()] = [] # empty measurements
    return r

  def __repr__(self):
    return "%s<%s>" % (self.__class__.__name__, self.name)

class Gauge(Metric):
  """Librato Gauge metric"""
  def add(self, value, source=None, **params):
    """Add a new measurement to this gauge"""
    return self.connection.send_gauge_value(self.name, value, source, **params)

  def what_am_i(self):
    return 'gauges'

class Counter(Metric):
  """Librato Counter metric"""
  def add(self, value, source=None, **params):
    return self.connection.send_counter_value(self.name, value, source, **params)

  def what_am_i(self):
    return 'counters'
