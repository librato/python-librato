import requests
import json

# Defaults
HOSTNAME  = "https://metrics-api.librato.com"
BASE_PATH = "/v1/"

class Metric():
  def __init__(self, connection, name, attributes=None, period=None, description=None):
    self.connection = connection
    self.name = name
    #self.attributes=attributes or {}
    #self.period = period
    self.description = description

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
    #obj.period      = data['period']
    #obj.attributes  = data['attributes']
    obj.description = data['description']

    return obj

class Gauge(Metric):
  """Librato Gauge metric"""

  def add(self, value, source=None, **params):
    """Add a new measurement to this gauge"""
    return self.connection.send_gauge_value(self.name, value, source, **params)

class Counter(Metric):
  """Librato Counter metric"""

  def add(self, value, source=None, **params):
    return self.connection.send_counter_value(self.name, value, source, **params)

class Connection(object):
  HOSTNAME  = "https://metrics-api.librato.com"
  BASE_PATH = "/v1/"

  def __init__(self, username, api_key, hostname=HOSTNAME, base_path=BASE_PATH):
    self.hostname  = hostname
    self.base_path = base_path
    self.auth      = (username, api_key)

  def _exe(self, end_path, query_params):
    url      = self.hostname + self.base_path + end_path
    response = requests.get(url, auth=self.auth, params=query_params)
    return json.loads(response.text)

  def _parse(self, resp, name, cls):
    if resp.has_key(name):
      return [cls.from_dict(self, m) for m in resp[name]]
    else:
      return resp

  def list_metrics(self, **query_params):
    r = self._exe(end_path="metrics", query_params=query_params)
    return self._parse(resp=r, name="metrics", cls=Metric)
