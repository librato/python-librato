from urlparse import urlparse
import urllib

class MockResponse(object):
  def __init__(self):
    self.text = ""

class MockRequest(object):
  def __init__(self):
    pass

  def show_request(self, url, params, fn_path):
    print("url requested  : %s" % url)
    print("params         : %s" % params)
    print("Loading fixture: %s" % fn_path)

  def get(self, url, auth, params):
    parsed       = urlparse(url)
    path, params = parsed.path, urllib.urlencode(params)
    f_name       = path.replace('/', '_')
    fn_path      = 'tests/fixtures/%s-%s.json' % (f_name, params)

    self.show_request(url, params, fn_path)

    fd           = open(fn_path)
    content      = fd.read()
    fd.close()
    resp         = MockResponse()
    resp.text    = content
    return resp

  def post(self, url, auth, data):
    """We don't need to do anything here. In the submit instance method
    for Metric, we will run set_payload(). After submit we can check the
    payload attribute.
    """
    pass
