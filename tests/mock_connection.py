from urlparse import urlparse
import urllib, json, re

class MockServer(object):
  """Mock the data storing in the backend"""
  def __init__(self):
    self.store    = {}
    self.gauges   = {}
    self.counters = {}

  def list_of_metrics(self):
    store = {}
    store['metrics'] = []
    for n, g in self.gauges.items():
      store['metrics'].append(g)
    for n, c in self.counters.items():
      store['metrics'].append(c)

    return json.dumps(store)

  def add_batch_of_measurements(self, gc_measurements):
    for gm in gc_measurements['gauges']:
      new_gauge = { 'name': gm['name'], 'type': gm['type'] }
      self.add_gauge_to_store(new_gauge)
      self.add_gauge_measurement(gm)

    #for cm in gc_measurements['counters']
      #self.add_single_gauge_measurement(cm['name'], cm)

  def add_single_gauge_measurement(self, gauge_name, m):
    m['name'] = gauge_name
    self.add_gauge_measurement(m)
    return ''

  def add_gauge_measurement(self, m):
    """Add a measuremnt to a gauge
       m = {*"source": "source_test", "value": 100}
       (*) source is optional
    """
    gauge_name  = m['name']
    pm          = self.gauges[gauge_name]['measurements'] # pointer to measurement
    self.add_default_source_if_needed(m)
    pm[m['source']].append(m)

  def add_default_source_if_needed(self, m):
    gauge_name  = m['name']
    pm          = self.gauges[gauge_name]['measurements'] # pointer to measurement
    source_name = 'unassigned' if not m.has_key('source') else m['source']
    if not pm.has_key(source_name): # source not there
      pm[source_name] = []
    m['source'] = 'unassigned'

  def create_gauge(self, new_gauge):
    """ new_gauge (body) should look like:
        {"name": "Test", "description": "Test Gauge to be removed"}
    """
    self.add_gauge_to_store(new_gauge)
    return json.dumps(new_gauge)

  def get_gauge(self, name):
    return json.dumps(self.gauges[name])

  def add_gauge_to_store(self, g):
    if not self.gauges.has_key(g['name']):
      g['type'] = 'gauge'
      if not g.has_key('period')    : g['period']     = None
      if not g.has_key('attributes'): g['attributes'] = {}
      g['measurements'] = {}
      self.gauges[g['name']] = g

  def delete_gauge(self, name):
    del self.gauges[name]
    return ''

'''Start the server.'''
server = MockServer()

class MockResponse(object):
  ''' Inspect the request and interact with the mocked server to generate
  and answer
  '''
  def __init__(self, request):
    self.request = request
    self.status  = 200

  def read(self):
    return self.json_body_based_on_request()

  def json_body_based_on_request(self):
    r = self.request
    if self.req_is_list_of_metrics():
      return server.list_of_metrics()
    elif self.req_is_create_gauge():
      return server.create_gauge(r.body)
    elif self.req_is_delete('gauges'):
      return server.delete_gauge(self.extract_from_url())
    elif self.req_is_get_gauge():
      return server.get_gauge(self.extract_from_url())
    elif self.req_is_send_value('gauges'):
      return server.add_single_gauge_measurement(self.extract_from_url(), r.body)
    elif self.req_is_send_batch_measurements():
      return server.add_batch_of_measurements(r.body)
    else:
      msg = """
      ----
      I am just mocking a RESTful Api server, I am not an actual server.
      path =  % s
      ----
      """ % self.request.uri
      raise Exception(msg)

  def req_is_send_batch_measurements(self):
    return self.method_is('POST') and self.path_is('/v1/metrics')

  def req_is_send_value(self, what):
    return self.method_is('POST') and re.match('/v1/%s/([\w_]+).json' % what, self.request.uri)

  def req_is_get_gauge(self):
    return self.method_is('GET') and re.match('/v1/gauges/([\w_]+).json', self.request.uri)

  def req_is_delete(self, what):
    return self.method_is('DELETE') and re.match('/v1/%s/([\w_]+).json' % what, self.request.uri)

  def req_is_list_of_metrics(self):
    return self.method_is('GET') and self.path_is('/v1/metrics.json')

  def req_is_create_gauge(self):
    return self.method_is('POST') and self.path_is('/v1/gauges.json')

  def method_is(self, m):
    return self.request.method == m

  def path_is(self,p):
    return self.request.uri == p

  def extract_from_url(self):
    m = re.match('/v1/gauges/([\w_]+).json', self.request.uri)
    try:
      name = m.group(1)
    except:
      raise
    return name

class MockConnect(object):
  """Mocks urllib's HTTPSConnection.
  These are the methods we use in _mexec
  .request(method, uri, body, headers) : perform the request
  .getresponse()                       : return response object.
    .status
    .read() -> raw json body of the answer
  """
  def __init__(self, hostname):
    self.hostname = hostname

  def request(self, method, uri, body, headers):
    self.method  = method
    self.uri     = uri
    self.headers = headers
    self.set_body(body)

  def set_body(self, b):
    self.body = json.loads(b) if b else b

  def getresponse(self):
    return MockResponse(self)
