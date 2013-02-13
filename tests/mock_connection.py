from urlparse import urlparse
from collections import defaultdict
import urllib, json, re

class MockServer(object):
  """Mock the data storing in the backend"""
  def __init__(self):
    self.clean()

  def clean(self):
    self.metrics = { 'gauges': {}, 'counters': {} }

  def list_of_metrics(self):
    answer = self.__an_empty_list_metrics()
    for gn, g in self.metrics['gauges'].items():
      answer['metrics'].append(g)
    for cn, c in self.metrics['counters'].items():
      answer['metrics'].append(c)
    return json.dumps(answer)

  def create_metric(self, payload):
    """ Check 3) in POST /metrics for payload example """
    #metric_type = self.find_type_of_metric(payload)[0:-1]

    for metric_type in ['gauge', 'counter']:
      for metric in payload[metric_type + 's']:
        name = metric['name']
        self.add_metric_to_store(metric, metric_type)

        # The metric comes also with a value, we have to add it
        # to the measurements (for a particular source if available)
        if metric.has_key('value'):
          if not metric.has_key('source'):
            source = 'unassigned'
          else:
            source = metric['source']
            del metric['source']
          value  = metric['value']
          del metric['value']

          # Create a new source for the measurements if necessary
          p_to_metric = self.metrics[metric_type + 's'][name]
          if not p_to_metric['measurements'].has_key(source):
            p_to_metric['measurements'][source] = []
          p_to_metric['measurements'][source].append({"value": value})

    return ''

  def get_metric(self, name, payload):
    gauges   = self.metrics['gauges']
    counters = self.metrics['counters']
    if gauges.has_key(name):
      metric = gauges[name]
    if counters.has_key(name):
      metric = counters[name]
    return json.dumps(metric)

  def delete_metric(self, payload):
    gauges   = self.metrics['gauges']
    counters = self.metrics['counters']
    if payload.has_key('names'):
      for rm_name in payload['names']:
        if gauges.has_key(rm_name):
          del gauges[rm_name]
        if counters.has_key(rm_name):
          del counters[rm_name]
    else:
      raise Exception('Trying to DELETE metric without providing array of names')
    return ''

  def __an_empty_list_metrics(self):
    answer = {}
    answer['metrics'] = []
    answer['query'] = {}
    return answer

  def add_batch_of_measurements(self, gc_measurements):
    for gm in gc_measurements['gauges']:
      new_gauge = { 'name': gm['name'], 'type': gm['type'] }
      self.add_gauge_to_store(new_gauge)
      self.add_gauge_measurement(gm)

  def add_metric_to_store(self, g, m_type):
    if not self.metrics[m_type + 's'].has_key(g['name']):
      g['type'] = m_type
      if not g.has_key('period')    : g['period']     = None
      if not g.has_key('attributes'): g['attributes'] = {}
      g['measurements'] = {}
      self.metrics[m_type + 's'][g['name']] = g

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
    elif self.req_is_create_metric():
      return server.create_metric(r.body)
    elif self.req_is_delete():
      return server.delete_metric(r.body)
    elif self.req_is_get_metric():
      return server.get_metric(self.extract_from_url(), r.body)
    else:
      msg = """
      ----
      I am just mocking a RESTful Api server, I am not an actual server.
      path = %s
      ----
      """ % self.request.uri
      raise Exception(msg)

  def req_is_list_of_metrics(self):
    return self.method_is('GET') and self.path_is('/v1/metrics')

  def req_is_create_metric(self):
    return self.method_is('POST') and self.path_is('/v1/metrics')

  def req_is_delete(self):
    return self.method_is('DELETE')

  def req_is_get_metric(self):
    return self.method_is('GET') and re.match('/v1/metrics/([\w_]+)', self.request.uri)

  def req_is_send_value(self, what):
    return self.method_is('POST') and re.match('/v1/%s/([\w_]+).json' % what, self.request.uri)

  def method_is(self, m):
    return self.request.method == m

  def path_is(self,p):
    return self.request.uri == p

  def extract_from_url(self):
    m = re.match('/v1/metrics/([\w_]+)', self.request.uri)
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
    self.body    = json.loads(body) if body else body

  def getresponse(self):
    return MockResponse(self)
