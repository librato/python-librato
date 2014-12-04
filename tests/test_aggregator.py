import logging
import unittest
import librato
from librato.aggregator import Aggregator
from mock_connection import MockConnect, server
#from random import randint

#logging.basicConfig(level=logging.DEBUG)
librato.HTTPSConnection = MockConnect


class TestAggregator(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')
        server.clean()
        self.agg = Aggregator(self.conn)

    def test_initialize_measurements(self):
        assert self.agg.measurements == {}

    def test_initialize_source(self):
        assert Aggregator(self.conn).source is None
        assert Aggregator(self.conn, 'my.source').source == 'my.source'

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
        assert meas['sum'] == 42+43+44
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

    def test_to_payload_no_source(self):
        self.agg.source = None
        self.agg.add('test.metric', 42)
        assert self.agg.to_payload() == {
            'gauges': [
                {'name': 'test.metric', 'count': 1, 'sum': 42, 'min': 42, 'max': 42}
             ]
        }

    # If 'value' is specified in the payload, the API will throw an error
    # This is because it must be calculated at the API via sum/count=avg
    def test_value_not_in_payload(self):
        self.agg.add('test.metric', 42)
        assert 'value' not in self.agg.to_payload()

    def test_clear(self):
        self.agg.add('test.metric', 42)
        assert len(self.agg.measurements) == 1
        self.agg.clear()
        assert len(self.agg.measurements) == 0

    def test_connection(self):
        assert self.agg.connection == self.conn

    def test_submit(self):
        self.agg.add('test.metric', 42)
        self.agg.add('test.metric', 10)
        self.agg.submit()


if __name__ == '__main__':
    unittest.main()
