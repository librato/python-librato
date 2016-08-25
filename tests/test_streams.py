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

    def test_init_transform_function(self):
        self.assertIsNone(Stream('my.metric').transform_function)
        self.assertEqual(Stream(transform_function='x/p*60').transform_function, 'x/p*60')

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

    def test_init_split_axis(self):
        self.assertIsNone(Stream().split_axis)
        self.assertTrue(Stream(split_axis=True).split_axis)
        self.assertFalse(Stream(split_axis=False).split_axis)

    def test_init_min_max(self):
        self.assertIsNone(Stream().min)
        self.assertIsNone(Stream().max)
        self.assertEqual(Stream(min=-2).min, -2)
        self.assertEqual(Stream(max=42).max, 42)

    def test_init_units(self):
        self.assertIsNone(Stream().units_short)
        self.assertIsNone(Stream().units_long)
        self.assertEqual(Stream(units_short='req/s').units_short, 'req/s')
        self.assertEqual(Stream(units_long='requests per second').units_long, 'requests per second')

    def test_init_color(self):
        self.assertIsNone(Stream().color)
        self.assertEqual(Stream(color='#f00').color, '#f00')

    def test_init_gap_detection(self):
        self.assertIsNone(Stream().gap_detection)
        self.assertTrue(Stream(gap_detection=True).gap_detection)
        self.assertFalse(Stream(gap_detection=False).gap_detection)

    # Adding this to avoid exceptions raised due to unknown Stream attributes
    def test_init_with_extra_attributes(self):
        attrs = {"color": "#f00", "something": "foo"}
        s = Stream(**attrs)
        # color is a known attribute
        self.assertEqual(s.color, '#f00')
        self.assertEqual(s.something, 'foo')

    def test_get_payload(self):
        self.assertEqual(Stream(metric='my.metric').get_payload(),
                         {'metric': 'my.metric', 'source': '*'})

    def test_payload_all_attributes(self):
        s = Stream(metric='my.metric', source='*', name='my display name',
                   type='gauge', id=1234,
                   group_function='min', summary_function='max',
                   transform_function='x/p', downsample_function='min',
                   period=60, split_axis=False,
                   min=0, max=42,
                   units_short='req/s', units_long='requests per second')
        payload = {
            'metric': 'my.metric',
            'source': '*',
            'name': 'my display name',
            'type': 'gauge',
            'id': 1234,
            'group_function': 'min',
            'summary_function': 'max',
            'transform_function': 'x/p',
            'downsample_function': 'min',
            'period': 60,
            'split_axis': False,
            'min': 0,
            'max': 42,
            'units_short': 'req/s',
            'units_long': 'requests per second'
        }
        self.assertEqual(s.get_payload(), payload)


if __name__ == '__main__':
    unittest.main()
