import librato

class TestConnection:
  def setUp(self):
    username    = "drio"
    api_key     = "ABCDEFG"
    hostname    = "localhost"
    base_path   = "/v1/metrics"
    self.libcon = librato.Connection(username, api_key, hostname, base_path)

  def test_init(self):
    assert type(self.libcon) is librato.Connection

