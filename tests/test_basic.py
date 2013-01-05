import logging
import sys, json, unittest, re
import librato
from mock_connection import MockConnect

logging.basicConfig(level=logging.DEBUG)
librato.HTTPSConnection = MockConnect

class TestLibrato(unittest.TestCase):
  def setUp(self):
    self.conn = librato.connect('user_test', 'key_test')

  def  _when_there_are_no_metrics(self):
    metrics = self.conn.list_metrics()
    assert len(metrics) == 0

  def _adding_a_gauge(self, name, desc):
    gauge = self.conn.create_gauge(name, desc)
    assert gauge.name == name
    assert gauge.description == desc
    assert gauge.attributes == {}
    assert gauge.period == None
    # Get all metrics
    metrics = self.conn.list_metrics()
    assert type(metrics[0]) == librato.metrics.Gauge
    assert metrics[0].name == 'Test'

  def _deleting_a_gauge(self, name):
    self.conn.delete_gauge(name)
    metrics = self.conn.list_metrics()
    assert len(metrics) == 0

  def _get_gauge(self, name):
    gauge = self.conn.get_gauge('Test')
    assert gauge.name == 'Test'
    assert gauge.description == 'A Test Gauge.'

  def _add_gauge_single_measurements(self, name):
    self.conn.send_gauge_value("Test", 100)
    gauge = self.conn.get_gauge(name, resolution=1, count=2)
    assert gauge.name == 'Test'
    assert gauge.description == 'A Test Gauge.'
    assert type(gauge.measurements) == dict
    assert gauge.measurements.has_key('unassigned')
    assert len(gauge.measurements['unassigned']) == 1
    assert gauge.measurements['unassigned'][0]['value'] == 100

    self.conn.send_gauge_value("Test", 222)
    gauge = self.conn.get_gauge(name, resolution=1, count=2)
    assert gauge.name == 'Test'
    assert gauge.description == 'A Test Gauge.'
    assert type(gauge.measurements) == dict
    assert gauge.measurements.has_key('unassigned')
    assert len(gauge.measurements['unassigned']) == 2
    assert gauge.measurements['unassigned'][0]['value'] == 100
    assert gauge.measurements['unassigned'][1]['value'] == 222

  def test_main(self):
    self._when_there_are_no_metrics()

    self._adding_a_gauge('Test', 'A Test Gauge.')
    self._deleting_a_gauge('Test')

    self._adding_a_gauge('Test', 'A Test Gauge.')
    self._get_gauge('Test')

    self._add_gauge_single_measurements('Test')

if __name__ == '__main__':
  unittest.main()
