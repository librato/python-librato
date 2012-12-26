import sys, json, unittest, re, urllib
from urlparse import urlparse
import librato

class MockResponse(object):
  def __init__(self):
    self.text = ""

class MockRequest(object):
  def __init__(self):
    pass

  def get(self, url, auth, params):
    parsed       = urlparse(url)
    path, params = parsed.path, urllib.urlencode(params)
    f_name       = path.replace('/', '_')
    fn_path      = 'tests/fixtures/%s-%s.json' % (f_name, params)
    print("url requested  : %s" % url)
    print("params         : %s" % params)
    print("Loading fixture: %s" % fn_path)

    fd           = open(fn_path)
    content      = fd.read()
    fd.close()
    resp         = MockResponse()
    resp.text    = content
    return resp

librato.connection.requests = MockRequest()

class TestMetrics(unittest.TestCase):
  def setUp(self):
    self.api = librato.Connection("drio", "abcdef")

  def tearDown(self):
    pass

  def test_init(self):
    assert type(self.api) == librato.Connection

  def test_get_list_all_metrics(self):
    results = self.api.list_metrics()
    assert type(results) == list
    assert len(results)  == 2
    for m in results:
      assert re.search('app_requests|server_temperature', m.name)

  def test_get_specific_metric(self):
    expected_name = 'app_requests'
    results = self.api.list_metrics(name=expected_name)
    assert len(results) == 1
    assert results[0].name == expected_name

if __name__ == '__main__':
  unittest.main()
