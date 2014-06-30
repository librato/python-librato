import logging
import unittest
import time
import librato
from librato.composite_metrics import CompositeMetric
from mock_connection import MockConnect, server

#logging.basicConfig(level=logging.DEBUG)
# Mock the server
librato.HTTPSConnection = MockConnect

class TestCompositeMetric(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')
        server.clean()
        self.compose = 's("testmetric", "*")'
        self.start_time = time.time()

    def test_init(self):
        c = CompositeMetric(self.conn, self.compose, 60, self.start_time)

    def test_get_composite(self):
        c = CompositeMetric(self.conn, self.compose, 60, self.start_time)
        data = c.get_composite()
        self.assertIsInstance(data, dict)
        self.assertIn('compose', data.keys())
        self.assertIn('measurements', data.keys())

    def test_load(self):
        c = CompositeMetric(self.conn, self.compose, 60, self.start_time)
        c.load()
        meas = c.measurements[0]
        self.assertIn('series', meas.keys())

    def test_series(self):
        c = CompositeMetric(self.conn, self.compose, 60, self.start_time)
        c.load()
        s = c.series()
        self.assertIsInstance(s, list)
        self.assertIn('value', s[0])
        self.assertIn('measure_time', s[0])
        c.values()

    def test_values(self):
        c = CompositeMetric(self.conn, self.compose, 60, self.start_time)
        c.load()
        s = c.series()
        first_value = s[0]['value']
        v = c.values()
        self.assertIsInstance(v, list)
        self.assertIn(first_value, v)

    def test_measure_times(self):
        c = CompositeMetric(self.conn, self.compose, 60, self.start_time)
        c.load()
        s = c.series()
        first_measure_time= s[0]['measure_time']
        t = c.measure_times()
        self.assertIsInstance(t, list)
        self.assertIn(first_measure_time, t)

