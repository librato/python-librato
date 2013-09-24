import logging
import unittest
import librato
from mock_connection import MockConnect, server

logging.basicConfig(level=logging.DEBUG)
# Mock the server
librato.HTTPSConnection = MockConnect


class TestLibrato(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')
        server.clean()

    def test_list_metrics_when_there_are_no_metrics(self):
        metrics = self.conn.list_metrics()
        assert len(metrics) == 0

    def test_list_metrics_adding_gauge(self):
        """ Notice that the api forces you to send a value even when you are
            just trying to create the metric without measurements."""
        self.conn.submit('gauge_1', 1, description='desc 1')
        self.conn.submit('gauge_2', 2, description='desc 2')
        # Get all metrics
        metrics = self.conn.list_metrics()

        assert len(metrics) == 2
        assert isinstance(metrics[0], librato.metrics.Gauge)
        assert metrics[0].name == 'gauge_1'
        assert metrics[0].description == 'desc 1'

        assert isinstance(metrics[1], librato.metrics.Gauge)
        assert metrics[1].name == 'gauge_2'
        assert metrics[1].description == 'desc 2'

    def test_list_metrics_adding_counter_metrics(self):
        self.conn.submit('c1', 10, 'counter', description='counter desc 1')
        self.conn.submit('c2', 20, 'counter', description='counter desc 2')
        # Get all metrics
        metrics = self.conn.list_metrics()

        assert len(metrics) == 2

        assert isinstance(metrics[0], librato.metrics.Counter)
        assert metrics[0].name == 'c1'
        assert metrics[0].description == 'counter desc 1'

        assert isinstance(metrics[1], librato.metrics.Counter)
        assert metrics[1].name == 'c2'
        assert metrics[1].description == 'counter desc 2'

    def test_list_metrics_adding_one_counter_one_gauge(self):
        self.conn.submit('gauge1', 10)
        self.conn.submit('counter2', 20, type='counter', description="desc c2")
        # Get all metrics
        metrics = self.conn.list_metrics()
        assert isinstance(metrics[0], librato.metrics.Gauge)
        assert metrics[0].name == 'gauge1'

        assert isinstance(metrics[1], librato.metrics.Counter)
        assert metrics[1].name == 'counter2'
        assert metrics[1].description == 'desc c2'

    def test_deleting_a_gauge(self):
        self.conn.submit('test', 100)
        assert len(self.conn.list_metrics()) == 1
        self.conn.delete('test')
        assert len(self.conn.list_metrics()) == 0

    def test_deleting_a_counter(self):
        self.conn.submit('test', 200, type='counter')
        assert len(self.conn.list_metrics()) == 1
        self.conn.delete('test')
        assert len(self.conn.list_metrics()) == 0

    def test_get_gauge_basic(self):
        name, desc = '1', 'desc 1'
        self.conn.submit(name, 10, description=desc)
        gauge = self.conn.get(name)
        assert isinstance(gauge, librato.metrics.Gauge)
        assert gauge.name == name
        assert gauge.description == desc
        assert len(gauge.measurements['unassigned']) == 1
        assert gauge.measurements['unassigned'][0]['value'] == 10

    def test_get_counter_basic(self):
        name, desc = 'counter1', 'count desc 1'
        self.conn.submit(name, 20, type='counter', description=desc)
        counter = self.conn.get(name)
        assert isinstance(counter, librato.metrics.Counter)
        assert counter.name == name
        assert counter.description == desc
        assert len(counter.measurements['unassigned']) == 1
        assert counter.measurements['unassigned'][0]['value'] == 20

    def test_send_single_measurements_for_gauge_with_source(self):
        name, desc, src = 'Test', 'A Test Gauge.', 'from_source'
        self.conn.submit(name, 10, description=desc, source=src)
        gauge = self.conn.get(name)
        assert gauge.name == name
        assert gauge.description == desc
        assert len(gauge.measurements[src]) == 1
        assert gauge.measurements[src][0]['value'] == 10

    def test_send_single_measurements_for_counter_with_source(self):
        name, desc, src = 'Test', 'A Test Counter.', 'from_source'
        self.conn.submit(name, 111, type='counter', description=desc, source=src)
        counter = self.conn.get(name)
        assert counter.name == name
        assert counter.description == desc
        assert len(counter.measurements[src]) == 1
        assert counter.measurements[src][0]['value'] == 111

if __name__ == '__main__':
    unittest.main()
