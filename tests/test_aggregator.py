import logging
import unittest
import librato
from librato.aggregator import Aggregator
from mock_connection import MockConnect, server
# from random import randint

# logging.basicConfig(level=logging.DEBUG)
librato.HTTPSConnection = MockConnect


class TestAggregator(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')
        server.clean()
        self.agg = Aggregator(self.conn)

    def test_initialize_measurements(self):
        assert self.agg.measurements == {}

    def test_no_tags(self):
        tags = self.agg.get_tags()
        assert len(tags) == 0

    def test_constructor_tags(self):
        agg = Aggregator(self.conn, tags={'sky': 'blue'})
        tags = agg.get_tags()

        assert len(tags) == 1
        assert 'sky' in tags
        assert tags['sky'] == 'blue'

    def test_add_tags(self):
        agg = Aggregator(self.conn, tags={'sky': 'blue'})
        agg.add_tags({'sky': 'red', 'coal': 'black'})
        tags = agg.get_tags()

        assert len(tags) == 2
        assert 'sky' in tags
        assert tags['sky'] == 'red'
        assert 'coal' in tags
        assert tags['coal'] == 'black'

    def test_set_tags(self):
        agg = Aggregator(self.conn, tags={'sky': 'blue'})
        agg.set_tags({'coal': 'black'})
        tags = agg.get_tags()

        assert len(tags) == 1
        assert 'coal' in tags
        assert tags['coal'] == 'black'

    def test_initialize_source(self):
        assert Aggregator(self.conn).source is None
        assert Aggregator(self.conn, source='my.source').source == 'my.source'

    def test_initialize_period(self):
        assert Aggregator(self.conn).period is None
        assert Aggregator(self.conn, period=300).period == 300

    def test_initialize_measure_time(self):
        assert Aggregator(self.conn).measure_time is None
        assert Aggregator(self.conn, measure_time=12345).measure_time == 12345

    def test_add_single_measurement(self):
        m = 'metric.one'
        self.agg.add(m, 3)
        meas = self.agg.measurements[m]
        assert meas['count'] == 1
        assert meas['sum'] == 3
        assert meas['min'] == 3
        assert meas['max'] == 3

    def test_add_multiple_measurements(self):
        m = 'metric.one'
        self.agg.add(m, 3.1)
        self.agg.add(m, 7.2)
        meas = self.agg.measurements[m]
        assert meas['count'] == 2
        assert meas['sum'] == 10.3
        assert meas['min'] == 3.1
        assert meas['max'] == 7.2

    def test_add_multiple_metrics(self):
        m1 = 'metric.one'
        self.agg.add(m1, 3.1)
        self.agg.add(m1, 7.2)

        m2 = 'metric.two'
        self.agg.add(m2, 42)
        self.agg.add(m2, 43)
        self.agg.add(m2, 44)

        meas = self.agg.measurements[m1]
        assert meas['count'] == 2
        assert meas['sum'] == 10.3
        assert meas['min'] == 3.1
        assert meas['max'] == 7.2

        meas = self.agg.measurements[m2]
        assert meas['count'] == 3
        assert meas['sum'] == 42 + 43 + 44
        assert meas['min'] == 42
        assert meas['max'] == 44

    # Only gauges are supported (not counters)
    def test_to_payload(self):
        self.agg.source = 'mysource'
        self.agg.add('test.metric', 42)
        self.agg.add('test.metric', 43)
        assert self.agg.to_payload() == {
            'gauges': [
                {'name': 'test.metric', 'count': 2, 'sum': 85, 'min': 42, 'max': 43}
            ],
            'source': 'mysource'
        }
        assert 'gauges' in self.agg.to_payload()
        assert 'counters' not in self.agg.to_payload()

    def test_to_payload_no_source(self):
        self.agg.source = None
        self.agg.add('test.metric', 42)

        assert self.agg.to_payload() == {
            'gauges': [
                {
                    'name': 'test.metric',
                    'count': 1,
                    'sum': 42,
                    'min': 42,
                    'max': 42
                }
            ]
        }

    # If 'value' is specified in the payload, the API will throw an error
    # This is because it must be calculated at the API via sum/count=avg
    def test_value_not_in_payload(self):
        self.agg.add('test.metric', 42)
        assert 'value' not in self.agg.to_payload()

    def test_clear_clears_measurements(self):
        self.agg.add('test.metric', 42)
        assert len(self.agg.measurements) == 1
        self.agg.clear()
        assert self.agg.measurements == {}

    def test_clear_clears_measure_time(self):
        self.agg.measure_time = 12345
        assert self.agg.measure_time
        self.agg.clear()
        assert self.agg.measure_time is None

    def test_connection(self):
        assert self.agg.connection == self.conn

    def test_submit(self):
        self.agg.add('test.metric', 42)
        self.agg.add('test.metric', 10)
        resp = self.agg.submit()
        # Doesn't return a body
        assert resp is None
        # Comes back empty
        assert self.agg.measurements == {}

    def test_period_default(self):
        assert Aggregator(self.conn).period is None

    def test_period_attribute(self):
        self.agg.period = 300
        assert self.agg.period == 300

    def test_measure_time_attribute(self):
        self.agg.measure_time = 1418838418
        assert self.agg.measure_time == 1418838418

    def test_measure_time_default(self):
        assert self.agg.measure_time is None

    def test_measure_time_in_payload(self):
        mt = 1418838418
        self.agg.measure_time = mt
        self.agg.period = None
        self.agg.add("foo", 42)
        assert 'measure_time' in self.agg.to_payload()
        assert self.agg.to_payload()['measure_time'] == mt

    def test_measure_time_not_in_payload(self):
        self.agg.measure_time = None
        self.agg.period = None
        self.agg.add("foo", 42)
        assert 'measure_time' not in self.agg.to_payload()

    def test_floor_measure_time(self):
        # 2014-12-17 17:46:58 UTC
        # should round to 2014-12-17 17:46:00 UTC
        # which is 1418838360
        self.agg.measure_time = 1418838418
        self.agg.period = 60
        assert self.agg.floor_measure_time() == 1418838360

    def test_floor_measure_time_period_only(self):
        self.agg.measure_time = None
        self.agg.period = 60
        # Grab wall time and floor to 60 resulting in no remainder
        assert self.agg.floor_measure_time() % 60 == 0

    def test_floor_measure_time_no_period(self):
        self.agg.measure_time = 1418838418
        self.agg.period = None
        # Just return the user-specified measure_time
        assert self.agg.floor_measure_time() == self.agg.measure_time

    def test_floor_measure_time_no_period_no_measure_time(self):
        self.agg.measure_time = None
        self.agg.period = None
        # Should return nothing
        assert self.agg.floor_measure_time() is None

    def test_floored_measure_time_in_payload(self):
        # 2014-12-17 17:46:58 UTC
        # should round to 2014-12-17 17:46:00 UTC
        # which is 1418838360
        # This will occur only if period is set
        self.agg.measure_time = 1418838418
        self.agg.period = 60
        assert self.agg.to_payload()['measure_time'] == 1418838360

    def test_submit_side_by_side(self):
        # Tagged and untagged measurements should be handled as separate
        self.agg.add_tags({'hostname': 'web-1'})
        self.agg.add('test.metric', 42)
        self.agg.add_tagged('test.metric', 10)
        self.agg.submit()

        gauge = self.conn.get('test.metric', duration=60)
        assert len(gauge.measurements['unassigned']) == 1

        resp = self.conn.get_tagged('test.metric', duration=60, tags_search="hostname=web-1")
        assert len(resp['series']) == 1


if __name__ == '__main__':
    unittest.main()
