import sys, json, unittest, re
from urlparse import urlparse
import librato

class MockResponse(object):
  def __init__(self):
    self.text = ""

class MockRequest(object):
  def __init__(self):
    pass

  def get(self, url, auth):
    f_name    = urlparse(url).path.replace('/', '_')
    fd        = open('tests/fixtures/%s.json' % f_name)
    content   = fd.read()
    fd.close()
    resp      = MockResponse()
    resp.text = content
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

if __name__ == '__main__':
  unittest.main()
