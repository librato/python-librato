import sys, json, unittest, re, time
import librato
from mock_connection import MockRequest

librato.connection.requests = MockRequest()

class TestMetrics(unittest.TestCase):
  def setUp(self):
    self.api = librato.Connection('drio', 'abcdef')
    self.my_gauge = librato.Gauge(self.api, name='home_temp', description='Temp. at home')

    # Create a metric(gauge) and add a couple of measurements
    self.now = time.time()
    g = self.my_gauge
    g.add(20.2, source="upstairs")
    g.add(20.0, name="dummy", source="downstairs", measure_time=self.now)

    # TODO: try counters ...

  def tearDown(self):
    pass

  def test_add_measurements(self):
    g = self.my_gauge

    assert len(g.measurements) == 2
    assert g.measurements[0].name         == 'home_temp'
    assert g.measurements[0].value        == 20.2
    assert g.measurements[0].source       == 'upstairs'

    assert g.measurements[1].name         == 'dummy'
    assert g.measurements[1].value        == 20.0
    assert g.measurements[1].source       == 'downstairs'
    assert g.measurements[1].measure_time == self.now

  def test_checking_type_of_metric(self):
    g = self.my_gauge
    assert g.what_type() == 'gauges'

  def test_submit_measurements(self):
    g = self.my_gauge
    g.submit()

    assert g.payload.has_key('gauges')
    m = g.payload['gauges'] # the measurements
    assert len(m) == 2

    #print json.dumps(g.payload)
    #assert 1 == 2
    # TODO: use fixture to check json payload
