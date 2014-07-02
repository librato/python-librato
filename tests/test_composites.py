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
        self.start_time = int(time.time())
        self.end_time = self.start_time + 3600
        self.c = CompositeMetric(self.conn,
                compose=self.compose,
                resolution=60,
                start_time=self.start_time)
        self.c.load()

    def test_init(self):
        assert CompositeMetric(self.conn, compose=self.compose, resolution=3600, start_time=self.start_time)
        assert CompositeMetric(self.conn, compose=self.compose, resolution=3600, start_time=self.start_time, end_time=None)
        assert CompositeMetric(self.conn, compose=self.compose, resolution=3600, start_time=self.start_time, end_time=self.end_time)

    def test_get_composite(self):
        data = self.c.get_composite()
        self.assertIsInstance(data, dict)
        self.assertIn('compose', data.keys())
        self.assertIn('measurements', data.keys())

    def test_load(self):
        meas = self.c.measurements[0]
        self.assertIn('series', meas.keys())

    def test_series(self):
        s = self.c.series()
        self.assertIsInstance(s, list)
        self.assertIsInstance(s[0], list)
        self.assertIn('value', s[0][0])
        self.assertIn('measure_time', s[0][0])

    def test_values(self):
        c = self.c
        s = c.series()
        first_value = s[0][0]['value']
        v = c.values()
        self.assertIsInstance(v, list)
        self.assertIsInstance(v[0], list)
        self.assertIn(first_value, v[0])

    def test_measure_times(self):
        c = self.c
        s = c.series()
        first_measure_time= s[0][0]['measure_time']
        t = c.measure_times()
        self.assertIsInstance(t, list)
        self.assertIsInstance(t[0], list)
        self.assertIn(first_measure_time, t[0])

