import logging
import sys, json, unittest, re
from random import randint
import librato
from mock_connection import MockConnect

logging.basicConfig(level=logging.DEBUG)
librato.HTTPSConnection = MockConnect

class TestLibrato(unittest.TestCase):
  def setUp(self):
    self.conn = librato.connect('user_test', 'key_test')
    self.q = self.conn.new_queue()

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

  def _submit_one_measurement_batch_mode(self):
    # Let's make sure we don't have any metric in the server
    metrics = self.conn.list_metrics()
    assert len(metrics) == 0

    q = self.q
    q.add('temperature', 22.1)
    q.submit()
    metrics = self.conn.list_metrics()
    assert len(metrics) == 1
    gauge = self.conn.get_gauge('temperature', resolution=1, count=2)
    assert gauge.name == 'temperature'
    assert gauge.description == None
    assert len(gauge.measurements['unassigned']) == 1

    q.add('temperature', 23)
    q.submit()
    metrics = self.conn.list_metrics()
    assert len(metrics) == 1
    gauge = self.conn.get_gauge('temperature', resolution=1, count=2)
    assert gauge.name == 'temperature'
    assert gauge.description == None
    assert len(gauge.measurements['unassigned']) == 2
    assert gauge.measurements['unassigned'][0]['value'] == 22.1
    assert gauge.measurements['unassigned'][1]['value'] == 23

    self.conn.delete_gauge('temperature')

  def _submit_tons_of_measurement_batch_mode(self):
    q = self.q
    metrics = self.conn.list_metrics()
    assert len(metrics) == 0

    for t in range(1, q.MAX_MEASUREMENTS_PER_CHUNK+1):
      q.add('temperature', t)
    q.submit()
    metrics = self.conn.list_metrics()
    assert len(metrics) == 1
    gauge = self.conn.get_gauge('temperature', resolution=1, count=q.MAX_MEASUREMENTS_PER_CHUNK+1)
    assert gauge.name == 'temperature'
    assert gauge.description == None
    for t in range(1, q.MAX_MEASUREMENTS_PER_CHUNK+1):
      assert gauge.measurements['unassigned'][t-1]['value'] == t

    for cl in range(1, q.MAX_MEASUREMENTS_PER_CHUNK+1):
      q.add('cpu_load', cl)
    q.submit()
    metrics = self.conn.list_metrics()
    assert len(metrics) == 2
    gauge = self.conn.get_gauge('cpu_load', resolution=1, count=q.MAX_MEASUREMENTS_PER_CHUNK+1)
    assert gauge.name == 'cpu_load'
    assert gauge.description == None
    for t in range(1, q.MAX_MEASUREMENTS_PER_CHUNK+1):
      assert gauge.measurements['unassigned'][t-1]['value'] == t

    self.conn.delete_gauge('temperature')
    self.conn.delete_gauge('cpu_load')

  def test_main(self):
    """
    I have to run each test sequencially so the different requests
    to the mocked server do not happen concurrently.
    To do that I have only one single test method so its contents
    are run sequencially.
    """
    self._when_there_are_no_metrics()

    self._adding_a_gauge('Test', 'A Test Gauge.')
    self._deleting_a_gauge('Test')

    self._adding_a_gauge('Test', 'A Test Gauge.')
    self._get_gauge('Test')

    # Previous Test gauge is still there ...
    self._add_gauge_single_measurements('Test')
    self._deleting_a_gauge('Test')

    # Now we don't have any metric in the server ...
    self._submit_one_measurement_batch_mode()
    self._submit_tons_of_measurement_batch_mode()

if __name__ == '__main__':
  unittest.main()
