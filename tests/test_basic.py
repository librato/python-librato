import logging
import sys, json, unittest, re
from random import randint
import librato
from mock_connection import MockConnect, server

logging.basicConfig(level=logging.DEBUG)
librato.HTTPSConnection = MockConnect

class TestLibrato(unittest.TestCase):
  def setUp(self):
    self.conn = librato.connect('user_test', 'key_test')
    server.clean()
    self.q = self.conn.new_queue()

  def test_when_there_are_no_metrics(self):
    metrics = self.conn.list_metrics()
    assert len(metrics) == 0

  def test_adding_a_gauge(self):
    name = 'Test'
    desc = 'A Test Gauge.'
    gauge = self.conn.create_gauge(name, desc)
    assert gauge.name == name
    assert gauge.description == desc
    assert gauge.attributes == {}
    assert gauge.period == None
    # Get all metrics
    metrics = self.conn.list_metrics()
    assert type(metrics[0]) == librato.metrics.Gauge
    assert metrics[0].name == 'Test'

  def test_deleting_a_gauge(self):
    name, desc = 'Test', 'A Test Gauge.'
    gauge = self.conn.create_gauge(name, desc)
    self.conn.delete_gauge(name)
    metrics = self.conn.list_metrics()
    assert len(metrics) == 0

  def test_get_gauge(self):
    name, desc = 'Test', 'A Test Gauge.'
    gauge = self.conn.create_gauge(name, desc)
    gauge = self.conn.get_gauge(name)
    assert gauge.name == name
    assert gauge.description == desc

  def test_add_gauge_single_measurements(self):
    name, desc = 'Test', 'A Test Gauge.'
    gauge = self.conn.create_gauge(name, desc)

    self.conn.send_gauge_value("Test", 100)
    gauge = self.conn.get_gauge(name, resolution=1, count=2)
    assert gauge.name == name
    assert gauge.description == desc
    assert type(gauge.measurements) == dict
    assert gauge.measurements.has_key('unassigned')
    assert len(gauge.measurements['unassigned']) == 1
    assert gauge.measurements['unassigned'][0]['value'] == 100

    self.conn.send_gauge_value(name, 222)
    gauge = self.conn.get_gauge(name, resolution=1, count=2)
    assert gauge.name == name
    assert gauge.description == desc
    assert type(gauge.measurements) == dict
    assert gauge.measurements.has_key('unassigned')
    assert len(gauge.measurements['unassigned']) == 2
    assert gauge.measurements['unassigned'][0]['value'] == 100
    assert gauge.measurements['unassigned'][1]['value'] == 222

  def test_submit_one_measurement_batch_mode(self):
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

  def test_submit_tons_of_measurement_batch_mode(self):
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

if __name__ == '__main__':
  unittest.main()
