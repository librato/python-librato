from measurements import Measurement

class Metric(object):
  def __init__(self, connection, name, attributes=None, period=None, description=None):
    self.connection = connection
    self.name = name
    self.attributes=attributes or {}
    self.period = period
    self.description = description

    self.measurements = []
    self.payload = {}

  @classmethod
  def from_dict(cls, connection, data):
    """Returns a metric object from a dictionary item,
       which is usually from librato's API"""
    if data.get('type') == "gauge":
      cls = Gauge
    elif data.get('type') == "counter":
      cls = Counter

    obj             = cls(connection, data['name'])
    obj.description = data['description']
    obj.description = data['description']
    obj.type        = data['type']
    obj.period      = data['period']     if data.has_key('period') else None
    obj.attributes  = data['attributes'] if data.has_key('attributes') else {}

    return obj

  def add(self, value, **params):
    """Add a new measurement to this Metric"""
    params['name'] = params['name'] if params.has_key('name') else self.name
    m = Measurement(value, **params)
    self.measurements.append(m)
    #return self.connection.send_gauge_value(self.name, value, source, **params)

  def submit(self):
    """Send measurements to librato"""
    self.prepare_payload()
    self.connection._exe(end_path="metrics", method="POST", payload=self.payload)

  def prepare_payload(self):
    """set the payload based on the current measurements"""
    pl = self.payload        # alias, less typing
    pl[self.what_type()] = []
    a = pl[self.what_type()] # alias
    for m in self.measurements:
      a.append(m.__dict__)   # add the hash version of the measu. object

class Gauge(Metric):
  """Librato Gauge metric"""
  def what_type(self):
    return 'gauges'

class Counter(Metric):
  """Librato Counter metric"""
  def what_type(self):
    return 'counters'
