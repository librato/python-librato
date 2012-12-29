import sys, json, unittest, re, time
import librato
from mock_connection import MockRequest
import helpers

librato.connection.requests = MockRequest()

class TestMetrics(unittest.TestCase):
  def setUp(self):
    self.api = librato.Connection('drio', 'abcdef')
    self.my_gauge = librato.Gauge(self.api, name='home_temp', description='Temp. at home')

    # make a POST /metrics with two measurements (gauges)
    self.now = 1356802172
    g = self.my_gauge
    g.add(20.2, source="upstairs")
    g.add(20.0, name="dummy", source="downstairs", measure_time=self.now)

    # Load the truth for that
    fd                = open("tests/fixtures/post_measurements_two_gauges.json")
    self.truth_post_1 = json.loads(fd.read())['gauges']
    fd.close()
    # TODO: exercise counters ...

  def tearDown(self):
    pass

  def test_add_measurements(self):
    g     = self.my_gauge
    m     = g.measurements # alias
    truth = self.truth_post_1

    assert len(g.measurements) == 2
    assert helpers.dicts_match(truth[0], m[0].__dict__)
    assert helpers.dicts_match(truth[1], m[1].__dict__)

  def test_checking_type_of_metric(self):
    g = self.my_gauge
    assert g.what_type() == 'gauges'

  def test_submit_two_gauges_measurements(self):
    g = self.my_gauge
    g.submit()

    assert g.payload.has_key('gauges')
    m = g.payload['gauges'] # the measurements
    assert len(m) == 2

    # contents
    truth = self.truth_post_1
    assert helpers.dicts_match(m[0], truth[0])
    assert helpers.dicts_match(m[1], truth[1])
