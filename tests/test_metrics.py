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
        self.conn.submit('gauge_1', 1, description='desc 1')
        self.conn.submit('gauge_2', 2, description='desc 2')
        # Get all metrics
        metrics = self.conn.list_metrics()

        self.assertEqual(len(metrics), 2)
        assert isinstance(metrics[0], librato.metrics.Gauge)
        assert metrics[0].name == 'gauge_1'
        assert metrics[0].description == 'desc 1'

        assert isinstance(metrics[1], librato.metrics.Gauge)
        assert metrics[1].name == 'gauge_2'
        assert metrics[1].description == 'desc 2'

    def test_deleting_a_gauge(self):
        self.conn.submit('test', 100)
        assert len(self.conn.list_metrics()) == 1
        self.conn.delete('test')
        assert len(self.conn.list_metrics()) == 0

    def test_get_gauge_basic(self):
        name, desc = '1', 'desc 1'
        self.conn.submit(name, 10, description=desc)
        gauge = self.conn.get_metric(name)
        assert isinstance(gauge, librato.metrics.Gauge)
        assert gauge.name == name
        assert gauge.description == desc
        assert len(gauge.measurements['unassigned']) == 1
        assert gauge.measurements['unassigned'][0]['value'] == 10

    def test_send_single_measurements_for_gauge_with_source(self):
        name, desc, src = 'Test', 'A Test Gauge.', 'from_source'
        self.conn.submit(name, 10, description=desc, source=src)
        gauge = self.conn.get(name)
        assert gauge.name == name
        assert gauge.description == desc
        assert len(gauge.measurements[src]) == 1
        assert gauge.measurements[src][0]['value'] == 10

    def test_add_in_gauge(self):
        name, desc, src = 'Test', 'A Test Gauge.', 'from_source'
        self.conn.submit(name, 10, description=desc, source=src)
        gauge = self.conn.get(name)
        assert gauge.name == name
        assert gauge.description == desc
        assert len(gauge.measurements[src]) == 1
        assert gauge.measurements[src][0]['value'] == 10

        gauge.add(1, source=src)

        gauge = self.conn.get(name)
        assert gauge.name == name
        assert gauge.description == desc
        assert len(gauge.measurements[src]) == 2
        assert gauge.measurements[src][-1]['value'] == 1

    def test_submit(self):
        mt1 = int(time.time()) - 5

        tags = {'hostname': 'web-1'}
        self.conn.submit('user_cpu', 20.2, time=mt1, tags=tags)

        resp = self.conn.get('user_cpu', duration=60, tags_search="hostname=web-1")

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
        self.conn.submit_tagged('user_cpu', 20.2, time=mt1, tags=tags)

        # Ensure 'company' and 'hostname' tags made it through
        for tags_search in ["hostname=web-1", "company=Librato"]:
            resp = self.conn.get_tagged('user_cpu', duration=60, tags_search=tags_search)

            assert len(resp['series']) == 1

            measurements = resp['series'][0]['measurements']
            assert len(measurements) == 1

            assert measurements[0]['time'] == mt1
            assert measurements[0]['value'] == 20.2


if __name__ == '__main__':
    unittest.main()
