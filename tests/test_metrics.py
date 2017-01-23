import logging
import unittest
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch
import librato
import time
from mock_connection import MockConnect, server

# logging.basicConfig(level=logging.DEBUG)
# Mock the server
librato.HTTPSConnection = MockConnect


class TestLibrato(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')
        server.clean()

    def test_list_metrics_when_there_are_no_metrics(self):
        metrics = self.conn.list_metrics()
        assert len(metrics) == 0

    def test_list_all_metrics(self):
        def mock_list(**args):
            offset = args['offset']
            length = args['length']
            # I don't care what the metrics are
            # this is about testing the logic and the calls
            result = [{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}]
            return result[offset:length + offset]

        expected_call_list = [({'length': 5, 'offset': 0},),
                              ({'length': 5, 'offset': 5},),
                              ({'length': 5, 'offset': 10},)]
        with patch.object(
                self.conn,
                'list_metrics',
        ) as list_prop:
            list_prop.side_effect = mock_list
            metrics = list(self.conn.list_all_metrics(length=5))
            assert len(metrics) == 12
            assert list_prop.call_count == 3
            assert list_prop.call_args_list == expected_call_list

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

    def test_list_metrics_adding_one_gauge(self):
        self.conn.submit('gauge1', 10)
        # Get all metrics
        metrics = self.conn.list_metrics()
        assert isinstance(metrics[0], librato.metrics.Gauge)
        assert metrics[0].name == 'gauge1'

    def test_deleting_a_gauge(self):
        self.conn.submit('test', 100)
        assert len(self.conn.list_metrics()) == 1
        self.conn.delete('test')
        assert len(self.conn.list_metrics()) == 0

    def test_deleting_a_batch_of_gauges(self):
        self.conn.submit('test', 100)
        self.conn.submit('test2', 100)
        assert len(self.conn.list_metrics()) == 2
        self.conn.delete(['test', 'test2'])
        assert len(self.conn.list_metrics()) == 0

    def test_get_gauge_basic(self):
        name, desc, tags = 'my_metric', 'desc 1', {'city': 'austin'}
        self.conn.submit(name, 10, description=desc, tags=tags)
        gauge = self.conn.get_metric(name, duration=60)
        assert isinstance(gauge, librato.metrics.Gauge)
        assert gauge.name == name
        assert gauge.description == desc

        data = self.conn.get(name, duration=60, tags=tags)
        assert len(data['series']) == 1
        assert data['series'][0]['measurements'][0]['value'] == 10

    def test_submit(self):
        mt1 = int(time.time()) - 5

        tags = {'hostname': 'web-1'}
        self.conn.submit('user_cpu', 20.2, time=mt1, tags=tags)

        resp = self.conn.get('user_cpu', duration=60, tags_search="hostname=web-1")
        assert len(resp['series']) == 1
        assert resp['series'][0].get('tags', {}) == tags

        # Same query using tags param instead
        resp = self.conn.get('user_cpu', duration=60, tags={'hostname': 'web-1'})
        assert len(resp['series']) == 1
        assert resp['series'][0].get('tags', {}) == tags

        measurements = resp['series'][0]['measurements']
        assert len(measurements) == 1

        assert measurements[0]['time'] == mt1
        assert measurements[0]['value'] == 20.2

    def test_merge_tags(self):
        mt1 = int(time.time()) - 5

        self.conn.set_tags({'company': 'Librato'})
        tags = {'hostname': 'web-1'}
        self.conn.submit('user_cpu', 20.2, time=mt1, tags=tags)

        # Ensure 'company' and 'hostname' tags made it through
        for tags_search in ["hostname=web-1", "company=Librato"]:
            resp = self.conn.get('user_cpu', duration=60, tags_search=tags_search)

            assert len(resp['series']) == 1

            measurements = resp['series'][0]['measurements']
            assert len(measurements) == 1

            assert measurements[0]['time'] == mt1
            assert measurements[0]['value'] == 20.2

if __name__ == '__main__':
    unittest.main()
