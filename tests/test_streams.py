import logging
import unittest
import librato
from librato.streams import Stream
from mock_connection import MockConnect, server

# logging.basicConfig(level=logging.DEBUG)
# Mock the server
librato.HTTPSConnection = MockConnect

class TestStreamModel(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')
        server.clean()

    def test_init_metric(self):
        self.assertEqual(Stream('my.metric').metric, 'my.metric')
        self.assertEqual(Stream(metric='my.metric').metric, 'my.metric')

    def test_init_source(self):
        self.assertEqual(Stream('my.metric', 'my.source').source, 'my.source')
        self.assertEqual(Stream(source='my.source').source, 'my.source')

    def test_init_composite(self):
        composite_formula = 's("my.metric", "*")'
        self.assertEqual(Stream(composite=composite_formula).composite, composite_formula)

    def test_source_defaults_to_all(self):
        self.assertEqual(Stream('my.metric').source, '*')

    def test_composite_defaults_to_none(self):
        self.assertIsNone(Stream('my.metric').composite)

    def test_init_group_function(self):
        self.assertIsNone(Stream('my.metric').group_function)
        self.assertEqual(Stream(group_function='max').group_function, 'max')

    def test_init_summary_function(self):
        self.assertIsNone(Stream('my.metric').summary_function)
        self.assertEqual(Stream(summary_function='min').summary_function, 'min')

    # For composites ONLY
    def test_init_downsample_function(self):
        self.assertIsNone(Stream('my.metric').downsample_function)
        self.assertEqual(Stream(downsample_function='sum').downsample_function, 'sum')

    def test_init_period(self):
        self.assertIsNone(Stream('my.metric').period)
        self.assertEqual(Stream(period=60).period, 60)

    # Not very useful but part of the API
    def test_init_type(self):
        self.assertIsNone(Stream().type)
        self.assertEqual(Stream(type='gauge').type, 'gauge')

    def test_get_payload(self):
        self.assertEqual(Stream('my.metric').get_payload(),
            {'metric': 'my.metric', 'source': '*'})

if __name__ == '__main__':
    unittest.main()
