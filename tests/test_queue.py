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
        q.add('user_cpu', 10)
        q.submit()

        # Measurement must inherit 'sky' tag from connection
        resp = self.conn.get('user_cpu', duration=60, tags_search="sky=blue")

        assert len(resp['series']) == 1
        assert resp['series'][0].get('tags', {}) == conn.get_tags()

        measurements = resp['series'][0]['measurements']
        assert len(measurements) == 1
        assert measurements[0]['value'] == 10

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
        assert len(q.tagged_chunks) == 1
        assert q._num_measurements_in_current_chunk() == 1

    def test_default_type_measurement(self):
        q = self.q
        q.add('temperature', 22.1)
        assert len(q._current_chunk()['measurements']) == 1

    def test_num_metrics_in_queue(self):
        q = self.q
        # With only one chunk
        for _ in range(q.MAX_MEASUREMENTS_PER_CHUNK - 10):
            q.add('temperature', randint(20, 30))
        assert q._num_measurements_in_queue() == 290
        # Now ensure multiple chunks
        for _ in range(100):
            q.add('num_requests', randint(100, 300))
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
        assert len(q.tagged_chunks) == 1
        assert q._num_measurements_in_current_chunk() == q.MAX_MEASUREMENTS_PER_CHUNK

        q.add('temperature', 40)  # damn is pretty hot :)
        assert q._num_measurements_in_current_chunk() == 1
        assert len(q.tagged_chunks) == 2

    def test_submit_context_manager(self):
        tags = {"host": "machine1"}
        try:
            with self.conn.new_queue() as q:
                q.add('temperature', 32, tags=tags)
                raise ValueError
        except ValueError:
            metric = self.conn.get_metric('temperature')
            data = self.conn.get('temperature', resolution=1, count=2, duration=60, tags=tags)
            assert metric.name == 'temperature'
            assert metric.description is None
            assert len(data['series'][0]['measurements']) == 1

    def test_submit_one_measurement_batch_mode(self):
        tags = {'city': 'barcelona'}
        q = self.q
        q.add('temperature', 22.1, tags=tags)
        q.submit()
        metrics = self.conn.list_metrics()
        assert len(metrics) == 1
        metric = self.conn.get_metric('temperature', resolution=1, count=2)
        assert metric.name == 'temperature'
        assert metric.description is None
        data = self.conn.get('temperature', resolution=1, count=2, duration=60, tags=tags)
        assert len(data['series'][0]['measurements']) == 1

        # Add another measurements for temperature
        q.add('temperature', 23, tags=tags)
        q.submit()
        metrics = self.conn.list_metrics()
        assert len(metrics) == 1
        metric = self.conn.get_metric('temperature', resolution=1, count=2)
        assert metric.name == 'temperature'
        assert metric.description is None
        data = self.conn.get('temperature', resolution=1, count=2, duration=60, tags=tags)
        assert len(data['series'][0]['measurements']) == 2
        assert data['series'][0]['measurements'][0]['value'] == 22.1
        assert data['series'][0]['measurements'][1]['value'] == 23

    def test_submit_tons_of_measurement_batch_mode(self):
        q = self.q
        metrics = self.conn.list_metrics()
        assert len(metrics) == 0

        tags = {'city': 'barcelona'}
        for t in range(1, q.MAX_MEASUREMENTS_PER_CHUNK + 1):
            q.add('temperature', t, tags=tags)
        q.submit()

        metrics = self.conn.list_metrics()
        assert len(metrics) == 1
        m = self.conn.get_metric('temperature', resolution=1, count=q.MAX_MEASUREMENTS_PER_CHUNK + 1)
        assert m.name == 'temperature'
        assert m.description is None

        data = self.conn.get('temperature', resolution=1, duration=60, tags=tags)
        measurements = data['series'][0]['measurements']
        for t in range(1, q.MAX_MEASUREMENTS_PER_CHUNK + 1):
            assert measurements[t - 1]['value'] == t

        tags = {'host': 'pollux'}
        for cl in range(1, q.MAX_MEASUREMENTS_PER_CHUNK + 1):
            q.add('cpu_load', cl, tags=tags)
        q.submit()

        metrics = self.conn.list_metrics()
        assert len(metrics) == 2

        m = self.conn.get_metric('cpu_load', resolution=1, count=q.MAX_MEASUREMENTS_PER_CHUNK + 1)
        assert m.name == 'cpu_load'
        assert m.description is None

        data = self.conn.get('cpu_load', resolution=1, duration=60, tags=tags)
        measurements = data['series'][0]['measurements']
        for t in range(1, q.MAX_MEASUREMENTS_PER_CHUNK + 1):
            assert measurements[t - 1]['value'] == t

    def test_add_aggregator(self):
        q = self.q
        tags = {'sky': 'blue'}
        a = Aggregator(self.conn, tags=tags, measure_time=123)
        a.add('foo', 42)
        a.add('bar', 37)
        q.add_aggregator(a)

        measurements = q.tagged_chunks[0]['measurements']
        names = [g['name'] for g in measurements]
        assert len(q.tagged_chunks) == 1
        assert 'foo' in names
        assert 'bar' in names

        assert measurements[0]['tags'] == tags
        assert measurements[1]['tags'] == tags

        # All gauges should have the same measure_time
        assert 'time' in measurements[0]
        assert 'time' in measurements[1]

        assert measurements[0]['time'] == 123
        assert measurements[1]['time'] == 123

    def test_submit(self):
        q = self.q
        tags = {'hostname': 'web-1'}
        q.set_tags(tags)

        mt1 = int(time.time()) - 5
        q.add('system_cpu', 3.2, time=mt1)
        assert q._num_measurements_in_queue() == 1
        q.submit()

        resp = self.conn.get('system_cpu', duration=60, tags_search="hostname=web-1")

        assert len(resp['series']) == 1
        assert resp['series'][0].get('tags', {}) == {'hostname': 'web-1'}

        measurements = resp['series'][0]['measurements']
        assert len(measurements) == 1

        assert measurements[0]['time'] == mt1
        assert measurements[0]['value'] == 3.2

    def test_measurement_level_tag(self):
        q = self.q
        q.set_tags({'hostname': 'web-1'})

        mt1 = int(time.time()) - 5
        q.add('system_cpu', 33.22, time=mt1, tags={"user": "james"})
        q.submit()

        # Ensure both tags get submitted
        for tag_search in ["hostname=web-1", "user=james"]:
            resp = self.conn.get('system_cpu', duration=60, tags_search=tag_search)

            assert len(resp['series']) == 1

            measurements = resp['series'][0]['measurements']
            assert len(measurements) == 1

            assert measurements[0]['time'] == mt1
            assert measurements[0]['value'] == 33.22

    def test_md_measurement_level_tag_supersedes(self):
        q = self.q
        q.set_tags({'hostname': 'web-1'})

        mt1 = int(time.time()) - 5
        q.add('system_cpu', 33.22, time=mt1, tags={"hostname": "web-2"})
        q.submit()

        # Ensure measurement-level tag takes precedence
        resp = self.conn.get('system_cpu', duration=60, tags_search="hostname=web-1")
        assert len(resp['series']) == 0

        resp = self.conn.get('system_cpu', duration=60, tags_search="hostname=web-2")
        assert len(resp['series']) == 1

        measurements = resp['series'][0]['measurements']
        assert len(measurements) == 1

        assert measurements[0]['time'] == mt1
        assert measurements[0]['value'] == 33.22

    def test_auto_submit_on_metric_count_2(self):
        q = self.conn.new_queue(auto_submit_count=2)

        q.add('tagged_cpu', 10, tags={'hostname': 'web-2'})
        q.add('tagged_cpu', 20, tags={'hostname': 'web-2'})

        resp = self.conn.get('tagged_cpu', duration=60, tags_search="hostname=web-2")
        assert len(resp['series'][0]['measurements']) == 2

    def queue_send_as_when_queue_has_tags(self):
        q = self.conn.new_queue(tags={'foo': 1})
        q.add('a_metric', 10)

        assert q._num_measurements_in_queue() == 1

        resp = self.conn.get('a_metric', duration=60, tags_search="foo=1")
        assert len(resp['series']) == 1

if __name__ == '__main__':
    unittest.main()
