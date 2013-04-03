from collections import defaultdict, OrderedDict
import urllib, json, re

class MockServer(object):
  """Mock the data storing in the backend"""
  def __init__(self):
    self.clean()

  def clean(self):
    self.metrics = { 'gauges': OrderedDict(), 'counters': OrderedDict() }

  def list_of_metrics(self):
    answer = self.__an_empty_list_metrics()
    for gn, g in self.metrics['gauges'].items():
      answer['metrics'].append(g)
    for cn, c in self.metrics['counters'].items():
      answer['metrics'].append(c)
    return json.dumps(answer).encode('utf-8')

  def create_metric(self, payload):
    """ Check 3) in POST /metrics for payload example """
    #metric_type = self.find_type_of_metric(payload)[0:-1]

    for metric_type in ['gauge', 'counter']:
      for metric in payload[metric_type + 's']:
        name = metric['name']
        self.add_metric_to_store(metric, metric_type)

        # The metric comes also with a value, we have to add it
        # to the measurements (for a particular source if available)
        if 'value' in metric:
          if 'source' not in metric:
            source = 'unassigned'
          else:
            source = metric['source']
            del metric['source']
          value  = metric['value']
          del metric['value']

          # Create a new source for the measurements if necessary
          p_to_metric = self.metrics[metric_type + 's'][name]
          if source not in p_to_metric['measurements']:
            p_to_metric['measurements'][source] = []
          p_to_metric['measurements'][source].append({"value": value})

    return ''

  def get_metric(self, name, payload):
    gauges   = self.metrics['gauges']
    counters = self.metrics['counters']
    if name in gauges:
      metric = gauges[name]
    if name in counters:
      metric = counters[name]
    return json.dumps(metric).encode('utf-8')

  def delete_metric(self, payload):
    gauges   = self.metrics['gauges']
    counters = self.metrics['counters']
    if 'names' in payload:
      for rm_name in payload['names']:
        if rm_name in gauges:
          del gauges[rm_name]
        if rm_name in counters:
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
    if g['name'] not in self.metrics[m_type + 's']:
      g['type'] = m_type
      if 'period' not in g    : g['period']     = None
      if 'attributes' not in g: g['attributes'] = {}
      g['measurements'] = {}
      self.metrics[m_type + 's'][g['name']] = g

  def delete_gauge(self, name):
    del self.gauges[name]
    return ''

'''Start the server.'''
server = MockServer()


class MockResponse(object):
  '''
  Inspect the request and interact with the mocked server to generate
  and answer.
  '''
  def __init__(self, request, fake_failure=False):
    self.request = request
    self.status  = 500 if fake_failure else 200

  class headers(object):
    @staticmethod
    def get_content_charset(default):
        return 'utf-8'

  def read(self):
    return self._json_body_based_on_request()

  def _json_body_based_on_request(self):
    r = self.request
    if self._req_is_list_of_metrics():
      return server.list_of_metrics()
    elif self._req_is_create_metric():
      return server.create_metric(r.body)
    elif self._req_is_delete():
      return server.delete_metric(r.body)
    elif self._req_is_get_metric():
      return server.get_metric(self._extract_from_url(), r.body)
    else:
      msg = """
      ----
      I am just mocking a RESTful Api server, I am not an actual server.
      path = %s
      ----
      """ % self.request.uri
      raise Exception(msg)

  def _req_is_list_of_metrics(self):
    return self._method_is('GET') and self._path_is('/v1/metrics')

  def _req_is_create_metric(self):
    return self._method_is('POST') and self._path_is('/v1/metrics')

  def _req_is_delete(self):
    return self._method_is('DELETE')

  def _req_is_get_metric(self):
    return self._method_is('GET') and re.match('/v1/metrics/([\w_]+)', self.request.uri)

  def _req_is_send_value(self, what):
    return self._method_is('POST') and re.match('/v1/%s/([\w_]+).json' % what, self.request.uri)

  def _method_is(self, m):
    return self.request.method == m

  def _path_is(self,p):
    return self.request.uri == p

  def _extract_from_url(self):
    m = re.match('/v1/metrics/([\w_]+)', self.request.uri)
    try:
      name = m.group(1)
    except:
      raise
    return name

class MockConnect(object):
  """
  Mocks urllib's HTTPSConnection.
  These are the methods we use in _mexec
  .request(method, uri, body, headers) : perform the request
  .getresponse()                       : return response object.
    .status
    .read() -> raw json body of the answer
  """
  def __init__(self, hostname, fake_n_errors=0):
    self.hostname      = hostname
    self.fake_n_errors = fake_n_errors

  def request(self, method, uri, body, headers):
    self.method  = method
    self.uri     = uri
    self.headers = headers
    self.body    = json.loads(body) if body else body

  def getresponse(self):
    if self.fake_n_errors > 0:
      fake_error = True
      self.fake_n_errors -= 1
    else:
      fake_error = False
    return MockResponse(self, fake_error)
