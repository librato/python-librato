import logging
import unittest
import librato
from mock_connection import MockConnect, server
from random import randint

logging.basicConfig(level=logging.DEBUG)
librato.HTTPSConnection = MockConnect


class TestLibratoQueue(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')
        server.clean()
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
            q.add('temperature', randint(20, 30))
        assert len(q.chunks) == 1
        assert q._num_measurements_in_current_chunk() == q.MAX_MEASUREMENTS_PER_CHUNK

        q.add('temperature', 40)  # damn is pretty hot :)
        assert q._num_measurements_in_current_chunk() == 1
        assert len(q.chunks) == 2

    def test_submit_one_measurement_batch_mode(self):
        q = self.q
        q.add('temperature', 22.1)
        q.submit()
        metrics = self.conn.list_metrics()
        assert len(metrics) == 1
        gauge = self.conn.get('temperature', resolution=1, count=2)
        assert gauge.name == 'temperature'
        assert gauge.description == None
        assert len(gauge.measurements['unassigned']) == 1

        # Add another measurements for temperature
        q.add('temperature', 23)
        q.submit()
        metrics = self.conn.list_metrics()
        assert len(metrics) == 1
        gauge = self.conn.get('temperature', resolution=1, count=2)
        assert gauge.name == 'temperature'
        assert gauge.description == None
        assert len(gauge.measurements['unassigned']) == 2
        assert gauge.measurements['unassigned'][0]['value'] == 22.1
        assert gauge.measurements['unassigned'][1]['value'] == 23

    def test_submit_tons_of_measurement_batch_mode(self):
        q = self.q
        metrics = self.conn.list_metrics()
        assert len(metrics) == 0

        for t in range(1, q.MAX_MEASUREMENTS_PER_CHUNK+1):
            q.add('temperature', t)
        q.submit()
        metrics = self.conn.list_metrics()
        assert len(metrics) == 1
        gauge = self.conn.get('temperature', resolution=1, count=q.MAX_MEASUREMENTS_PER_CHUNK+1)
        assert gauge.name == 'temperature'
        assert gauge.description == None
        for t in range(1, q.MAX_MEASUREMENTS_PER_CHUNK+1):
            assert gauge.measurements['unassigned'][t-1]['value'] == t

        for cl in range(1, q.MAX_MEASUREMENTS_PER_CHUNK+1):
            q.add('cpu_load', cl)
        q.submit()
        metrics = self.conn.list_metrics()
        assert len(metrics) == 2
        gauge = self.conn.get('cpu_load', resolution=1, count=q.MAX_MEASUREMENTS_PER_CHUNK+1)
        assert gauge.name == 'cpu_load'
        assert gauge.description == None
        for t in range(1, q.MAX_MEASUREMENTS_PER_CHUNK+1):
            assert gauge.measurements['unassigned'][t-1]['value'] == t

if __name__ == '__main__':
    unittest.main()
