import logging
import unittest
import librato
from librato.aggregator import Aggregator
from mock_connection import MockConnect, server
from random import randint
import time

# logging.basicConfig(level=logging.DEBUG)
librato.HTTPSConnection = MockConnect


class TestLibratoQueue(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')
        server.clean()
        self.q = self.conn.new_queue()

    def test_empty_queue(self):
        q = self.q
        assert len(q.chunks) == 0
        assert q._num_measurements_in_current_chunk() == 0

    def test_no_tags(self):
        q = self.q
        assert len(q.get_tags()) == 0

    def test_inherited_tags(self):
        conn = librato.connect('user_test', 'key_test', tags={'sky': 'blue'})
        assert conn.get_tags() == {'sky': 'blue'}

        q = conn.new_queue()
        q.add_tagged('user_cpu', 10)
        q.submit()

        # Measurement must inherit 'sky' tag from connection
        resp = self.conn.get_tagged('user_cpu', duration=60, tags_search="sky=blue")

        assert len(resp['series']) == 1
        assert resp['series'][0].get('tags', {}) == conn.get_tags()

        measurements = resp['series'][0]['measurements']
        assert len(measurements) == 1
        assert measurements[0]['value'] == 10

    def test_inherit_connection_level_tags(self):
        """test if top level tags are ignored when passing measurement level tags"""
        conn = librato.connect('user_test', 'key_test', tags={'sky': 'blue'})

        q = conn.new_queue()
        q.add_tagged('user_cpu', 10, tags={"hi": "five"}, inherit_tags=True)

        measurements = q.tagged_chunks[0]['measurements']

        assert len(measurements) == 1
        assert measurements[0].get('tags', {}) == {'sky': 'blue', 'hi': 'five'}

    def test_ignore_connection_queue_level_tags(self):
        """test if queue level tags are ignored when passing measurement level tags"""
        conn = librato.connect('user_test', 'key_test', tags={'sky': 'blue'})

        q = conn.new_queue(tags={"service": "api"})
        q.add_tagged('user_cpu', 10, tags={"hi": "five"})
        measurements = q.tagged_chunks[0]['measurements']

        assert len(measurements) == 1
        assert measurements[0].get('tags', {}) == {'hi': 'five'}

        q.submit()

        resp = self.conn.get_tagged('user_cpu', duration=60, tags_search="sky=blue")
        assert len(resp['series']) == 0

    def test_inherit_connection_level_tags_through_add(self):
        """test if connection level tags are recognized when using the add function"""
        conn = librato.connect('user_test', 'key_test', tags={'sky': 'blue', 'company': 'Librato'})

        q = conn.new_queue()
        q.add('user_cpu', 100)
        measurements = q.tagged_chunks[0]['measurements']

        assert len(measurements) == 1
        assert measurements[0].get('tags', {}) == {'sky': 'blue', 'company': 'Librato'}

    def test_inherit_queue_connection_level_tags(self):
        """test if queue level tags are ignored when passing measurement level tags"""
        conn = librato.connect('user_test', 'key_test', tags={'sky': 'blue', 'company': 'Librato'})

        q = conn.new_queue(tags={"service": "api", "hi": "four", "sky": "red"})
        q.add_tagged('user_cpu', 100, tags={"hi": "five"}, inherit_tags=True)
        measurements = q.tagged_chunks[0]['measurements']

        assert len(measurements) == 1
        assert measurements[0].get('tags', {}) == {'sky': 'red', 'service': 'api', 'hi': 'five', 'company': 'Librato'}

    def test_inherit_queue_level_tags(self):
        """test if queue level tags are ignored when passing measurement level tags"""
        conn = librato.connect('user_test', 'key_test')

        q = conn.new_queue(tags={"service": "api", "hi": "four"})
        q.add_tagged('user_cpu', 100, tags={"hi": "five"}, inherit_tags=True)
        measurements = q.tagged_chunks[0]['measurements']

        assert len(measurements) == 1
        assert measurements[0].get('tags', {}) == {'service': 'api', 'hi': 'five'}

    def test_constructor_tags(self):
        conn = librato.connect('user_test', 'key_test', tags={'sky': 'blue'})
        q = conn.new_queue(tags={'sky': 'red', 'coal': 'black'})
        tags = q.get_tags()

        assert len(tags) == 2
        assert 'sky' in tags
        assert tags['sky'] == 'red'
        assert 'coal' in tags
        assert tags['coal'] == 'black'

    def test_add_tags(self):
        q = self.q
        q.add_tags({'mercury': 'silver'})
        tags = q.get_tags()

        assert len(tags) == 1
        assert 'mercury' in tags
        assert tags['mercury'] == 'silver'

    def test_set_tags(self):
        q = self.q
        q.add_tags({'mercury': 'silver'})

        q.set_tags({'sky': 'blue', 'mercury': 'silver'})
        tags = q.get_tags()

        assert len(tags) == 2
        assert 'sky' in tags
        assert tags['sky'] == 'blue'
        assert 'mercury' in tags
        assert tags['mercury'] == 'silver'

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

    def test_num_metrics_in_queue(self):
        q = self.q
        # With only one chunk
        for _ in range(q.MAX_MEASUREMENTS_PER_CHUNK - 10):
            q.add('temperature', randint(20, 30))
        assert q._num_measurements_in_queue() == 290
        # Now ensure multiple chunks
        for _ in range(100):
            q.add('num_requests', randint(100, 300), type='counter')
        assert q._num_measurements_in_queue() == 390

    def test_auto_submit_on_metric_count(self):
        q = self.conn.new_queue(auto_submit_count=10)
        for _ in range(9):
            q.add('temperature', randint(20, 30))
        assert q._num_measurements_in_queue() == 9
        metrics = self.conn.list_metrics()
        assert len(metrics) == 0
        q.add('temperature', randint(20, 30))
        assert q._num_measurements_in_queue() == 0
        metrics = self.conn.list_metrics()
        assert len(metrics) == 1

    def test_reach_chunk_limit(self):
        q = self.q
        for i in range(1, q.MAX_MEASUREMENTS_PER_CHUNK + 1):
            q.add('temperature', randint(20, 30))
        assert len(q.chunks) == 1
        assert q._num_measurements_in_current_chunk() == q.MAX_MEASUREMENTS_PER_CHUNK

        q.add('temperature', 40)  # damn is pretty hot :)
        assert q._num_measurements_in_current_chunk() == 1
        assert len(q.chunks) == 2

    def test_submit_context_manager(self):
        try:
            with self.conn.new_queue() as q:
                q.add('temperature', 32)
                raise ValueError
        except ValueError:
            gauge = self.conn.get('temperature', resolution=1, count=2)
            assert gauge.name == 'temperature'
            assert gauge.description is None
            assert len(gauge.measurements['unassigned']) == 1

    def test_submit_one_measurement_batch_mode(self):
        q = self.q
        q.add('temperature', 22.1)
        q.submit()
        metrics = self.conn.list_metrics()
        assert len(metrics) == 1
        gauge = self.conn.get('temperature', resolution=1, count=2)
        assert gauge.name == 'temperature'
        assert gauge.description is None
        assert len(gauge.measurements['unassigned']) == 1

        # Add another measurements for temperature
        q.add('temperature', 23)
        q.submit()
        metrics = self.conn.list_metrics()
        assert len(metrics) == 1
        gauge = self.conn.get('temperature', resolution=1, count=2)
        assert gauge.name == 'temperature'
        assert gauge.description is None
        assert len(gauge.measurements['unassigned']) == 2
        assert gauge.measurements['unassigned'][0]['value'] == 22.1
        assert gauge.measurements['unassigned'][1]['value'] == 23

    def test_submit_tons_of_measurement_batch_mode(self):
        q = self.q
        metrics = self.conn.list_metrics()
        assert len(metrics) == 0

        for t in range(1, q.MAX_MEASUREMENTS_PER_CHUNK + 1):
            q.add('temperature', t)
        q.submit()
        metrics = self.conn.list_metrics()
        assert len(metrics) == 1
        gauge = self.conn.get('temperature', resolution=1, count=q.MAX_MEASUREMENTS_PER_CHUNK + 1)
        assert gauge.name == 'temperature'
        assert gauge.description is None
        for t in range(1, q.MAX_MEASUREMENTS_PER_CHUNK + 1):
            assert gauge.measurements['unassigned'][t - 1]['value'] == t

        for cl in range(1, q.MAX_MEASUREMENTS_PER_CHUNK + 1):
            q.add('cpu_load', cl)
        q.submit()
        metrics = self.conn.list_metrics()
        assert len(metrics) == 2
        gauge = self.conn.get('cpu_load', resolution=1, count=q.MAX_MEASUREMENTS_PER_CHUNK + 1)
        assert gauge.name == 'cpu_load'
        assert gauge.description is None
        for t in range(1, q.MAX_MEASUREMENTS_PER_CHUNK + 1):
            assert gauge.measurements['unassigned'][t - 1]['value'] == t

    def test_add_aggregator(self):
        q = self.q
        metrics = self.conn.list_metrics()
        a = Aggregator(self.conn, source='mysource', period=10)
        a.add('foo', 42)
        a.add('bar', 37)
        q.add_aggregator(a)

        gauges = q.chunks[0]['gauges']
        names = [g['name'] for g in gauges]

        assert len(q.chunks) == 1

        assert 'foo' in names
        assert 'bar' in names

        # All gauges should have the same source
        assert gauges[0]['source'] == 'mysource'
        assert gauges[1]['source'] == 'mysource'

        # All gauges should have the same measure_time
        assert 'measure_time' in gauges[0]
        assert 'measure_time' in gauges[1]

        # Test that time was snapped to 10s
        assert gauges[0]['measure_time'] % 10 == 0

    def test_md_submit(self):
        q = self.q
        q.set_tags({'hostname': 'web-1'})

        mt1 = int(time.time()) - 5
        q.add_tagged('system_cpu', 3.2, time=mt1)
        assert q._num_measurements_in_queue() == 1
        q.submit()

        resp = self.conn.get_tagged('system_cpu', duration=60, tags_search="hostname=web-1")

        assert len(resp['series']) == 1
        assert resp['series'][0].get('tags', {}) == {'hostname': 'web-1'}

        measurements = resp['series'][0]['measurements']
        assert len(measurements) == 1

        assert measurements[0]['time'] == mt1
        assert measurements[0]['value'] == 3.2

    def test_md_measurement_level_tag(self):
        q = self.q
        q.set_tags({'hostname': 'web-1'})

        mt1 = int(time.time()) - 5
        q.add_tagged('system_cpu', 33.22, time=mt1, tags={"user": "james"}, inherit_tags=True)
        q.submit()

        # Ensure both tags get submitted
        for tag_search in ["hostname=web-1", "user=james"]:
            resp = self.conn.get_tagged('system_cpu', duration=60, tags_search=tag_search)

            assert len(resp['series']) == 1

            measurements = resp['series'][0]['measurements']
            assert len(measurements) == 1

            assert measurements[0]['time'] == mt1
            assert measurements[0]['value'] == 33.22

    def test_md_measurement_level_tag_supersedes(self):
        q = self.q
        q.set_tags({'hostname': 'web-1'})

        mt1 = int(time.time()) - 5
        q.add_tagged('system_cpu', 33.22, time=mt1, tags={"hostname": "web-2"})
        q.submit()

        # Ensure measurement-level tag takes precedence
        resp = self.conn.get_tagged('system_cpu', duration=60, tags_search="hostname=web-1")
        assert len(resp['series']) == 0

        resp = self.conn.get_tagged('system_cpu', duration=60, tags_search="hostname=web-2")
        assert len(resp['series']) == 1

        measurements = resp['series'][0]['measurements']
        assert len(measurements) == 1

        assert measurements[0]['time'] == mt1
        assert measurements[0]['value'] == 33.22

    def test_side_by_side(self):
        # Ensure tagged and untagged measurements are handled independently
        q = self.conn.new_queue(tags={'hostname': 'web-1'})

        q.add('system_cpu', 10)
        q.add_tagged('system_cpu', 20)
        q.submit()

        resp = self.conn.get_tagged('system_cpu', duration=60, tags_search="hostname=web-1")
        assert len(resp['series']) == 1

        measurements = resp['series'][0]['measurements']
        assert len(measurements) == 2
        assert measurements[0]['value'] == 10
        assert measurements[1]['value'] == 20

    def test_md_auto_submit_on_metric_count(self):
        q = self.conn.new_queue(auto_submit_count=2)

        q.add('untagged_cpu', 10)
        q.add_tagged('tagged_cpu', 20, tags={'hostname': 'web-2'})

        assert q._num_measurements_in_queue() == 0

        gauge = self.conn.get('untagged_cpu', duration=60)
        assert len(gauge.measurements['unassigned']) == 1

        resp = self.conn.get_tagged('tagged_cpu', duration=60, tags_search="hostname=web-2")
        assert len(resp['series']) == 1

    def queue_send_as_md_when_queue_has_tags(self):
        q = self.conn.new_queue(tags={'foo': 1})
        q.add('a_metric', 10)

        assert q._num_measurements_in_queue() == 1

        resp = self.conn.get_tagged('a_metric', duration=60, tags_search="foo=1")
        assert len(resp['series']) == 1

    def test_transparent_submit_md(self):
        q = self.q
        tags = {'hostname': 'web-1'}

        mt1 = int(time.time()) - 5
        q.add('system_cpu', 3.2, time=mt1, tags=tags)
        assert q._num_measurements_in_queue() == 1
        q.submit()

        resp = self.conn.get_tagged('system_cpu', duration=60, tags_search="hostname=web-1")

        assert len(resp['series']) == 1
        assert resp['series'][0].get('tags', {}) == {'hostname': 'web-1'}

        measurements = resp['series'][0]['measurements']
        assert len(measurements) == 1

        assert measurements[0]['time'] == mt1
        assert measurements[0]['value'] == 3.2

if __name__ == '__main__':
    unittest.main()
