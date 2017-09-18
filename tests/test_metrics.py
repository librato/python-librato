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

fake_metric = {
    "name": "3333",
    "display_name": "test name",
    "type": "gauge",
    "attributes": {
        "created_by_ua": "fake",
    },
    "description": "a description",
    "period": 60,
    "source_lag": 60
}


class TestLibrato(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')
        server.clean()

    def test_list_metrics_when_there_are_no_metrics(self):
        metrics = self.conn.list_metrics()
        assert len(metrics) == 0

    def test_list_all_metrics(self):
        def mock_list(entity, query_props=None):
            length = query_props['length']
            offset = query_props['offset']
            # I don't care what the metrics are
            # this is about testing the logic and the calls
            result = [fake_metric for x in range(12)]
            return {
                    "query":
                    {
                        "offset": offset,
                        "length": length,
                        "found": 12,
                        "total": 12
                    },
                    "metrics": result[offset:length + offset]
                   }

        with patch.object(
                self.conn,
                '_mexe',
        ) as list_prop:
            list_prop.side_effect = mock_list
            metrics = list(self.conn.list_all_metrics(length=5, offset=0))
            assert len(metrics) == 12
            assert list_prop.call_count == 3

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

    def test_deleting_a_batch_of_gauges(self):
        self.conn.submit('test', 100)
        self.conn.submit('test2', 100)
        assert len(self.conn.list_metrics()) == 2
        self.conn.delete(['test', 'test2'])
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

    def test_add_in_counter(self):
        name, desc, src = 'Test', 'A Test Counter.', 'from_source'
        self.conn.submit(name, 111, type='counter', description=desc, source=src)
        counter = self.conn.get(name)
        assert counter.name == name
        assert counter.description == desc
        assert len(counter.measurements[src]) == 1
        assert counter.measurements[src][0]['value'] == 111

        counter.add(1, source=src)

        counter = self.conn.get(name)
        assert counter.name == name
        assert counter.description == desc
        assert len(counter.measurements[src]) == 2
        assert counter.measurements[src][-1]['value'] == 1

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

    def test_md_inherit_tags(self):
        self.conn.set_tags({'company': 'Librato', 'hi': 'four'})

        measurement = self.conn.create_tagged_payload('user_cpu', 20.2, tags={'hi': 'five'}, inherit_tags=True)

        assert measurement['tags'] == {'hi': 'five', 'company': 'Librato'}

    def test_md_donot_inherit_tags(self):
        self.conn.set_tags({'company': 'Librato', 'hi': 'four'})

        measurement = self.conn.create_tagged_payload('user_cpu', 20.2, tags={'hi': 'five'})

        assert measurement['tags'] == {'hi': 'five'}

    def test_md_submit(self):
        mt1 = int(time.time()) - 5

        tags = {'hostname': 'web-1'}
        self.conn.submit_tagged('user_cpu', 20.2, time=mt1, tags=tags)

        resp = self.conn.get_tagged('user_cpu', duration=60, tags_search="hostname=web-1")
        assert len(resp['series']) == 1
        assert resp['series'][0].get('tags', {}) == tags

        # Same query using tags param instead
        resp = self.conn.get_tagged('user_cpu', duration=60, tags={'hostname': 'web-1'})
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
        self.conn.submit_tagged('user_cpu', 20.2, time=mt1, tags=tags, inherit_tags=True)

        # Ensure 'company' and 'hostname' tags made it through
        for tags_search in ["hostname=web-1", "company=Librato"]:
            resp = self.conn.get_tagged('user_cpu', duration=60, tags_search=tags_search)

            assert len(resp['series']) == 1

            measurements = resp['series'][0]['measurements']
            assert len(measurements) == 1

            assert measurements[0]['time'] == mt1
            assert measurements[0]['value'] == 20.2

    def test_submit_transparent_tagging(self):
        mt1 = int(time.time()) - 5

        tags = {'hostname': 'web-1'}
        self.conn.submit('user_cpu', 20.2, time=mt1, tags=tags)

        resp = self.conn.get_tagged('user_cpu', duration=60, tags_search="hostname=web-1")

        assert len(resp['series']) == 1
        assert resp['series'][0].get('tags', {}) == tags

        measurements = resp['series'][0]['measurements']
        assert len(measurements) == 1

        assert measurements[0]['time'] == mt1
        assert measurements[0]['value'] == 20.2

if __name__ == '__main__':
    unittest.main()
