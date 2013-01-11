import logging
import sys, json, unittest, re
import librato
from mock_connection import MockConnect
from random import randint

logging.basicConfig(level=logging.DEBUG)
librato.HTTPSConnection = MockConnect

class TestLibratoQueue(unittest.TestCase):
  def setUp(self):
    self.conn = librato.connect('user_test', 'key_test')
    self.q = self.conn.new_queue()

  def test_empty_queue(self):
    q = self.q
    assert len(q.chunks) == 1
    assert q._num_measurements_in_current_chunk() == 0

  def test_single_measurement_gauge(self):
    q = self.q
    q.add('temperature', 22.1)
    assert len(q.chunks) == 1
    assert q._num_measurements_in_current_chunk() == 1

  def test_default_type_measurement(self):
    q = self.q
    q.add('temperature', 22.1)
    assert len(q._current_chunk()['gauges']) == 1
    assert len(q._current_chunk()['counters']) == 0

  def test_single_measurement_counter(self):
    q = self.q
    q.add('num_requests', 2000, type='counter')
    assert len(q.chunks) == 1
    assert q._num_measurements_in_current_chunk() == 1
    assert len(q._current_chunk()['gauges']) == 0
    assert len(q._current_chunk()['counters']) == 1

  def test_reach_chunk_limit(self):
    q = self.q
    for i in range(1, q.MAX_MEASUREMENTS_PER_CHUNK+1):
      q.add('temperature', randint(20,30))
    assert len(q.chunks) == 1
    assert q._num_measurements_in_current_chunk() == q.MAX_MEASUREMENTS_PER_CHUNK

    q.add('temperature', 40) # damn is pretty hot :)
    assert q._num_measurements_in_current_chunk() == 1
    assert len(q.chunks) == 2


