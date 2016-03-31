import logging
import unittest
import librato
from librato import Space, Chart
from librato.streams import Stream
from mock_connection import MockConnect, server

# logging.basicConfig(level=logging.DEBUG)
# Mock the server
librato.HTTPSConnection = MockConnect

class ChartsTest(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')
        server.clean()

# Charts
class TestChartsConnection(ChartsTest):
    def setUp(self):
        super(TestChartsConnection, self).setUp()
        self.space = self.conn.create_space("My Space")

    def test_connection(self):
        self.assertEqual(Chart(self.conn, 'cpu').connection, self.conn)

    def test_chart_name(self):
        self.assertEqual(Chart(self.conn, 'cpu').name, 'cpu')

    def test_space_id(self):
        self.assertEqual(Chart(self.conn, 'cpu', space_id=42).space_id, 42)

    def test_space_attribute(self):
        chart = Chart(self.conn, 'cpu')
        chart._space = self.space
        self.assertEqual(chart._space, self.space)

    def test_chart_type(self):
        # Debated `chart_type` vs `type`, going with `type`
        self.assertEqual(Chart(self.conn, 'cpu', type='line').type, 'line')
        self.assertEqual(Chart(self.conn, 'cpu', type='stacked').type, 'stacked')
        self.assertEqual(Chart(self.conn, 'cpu', type='bignumber').type, 'bignumber')

    def test_create_chart_without_streams(self):
        chart_name = "Empty Chart"
        chart = self.conn.create_chart(chart_name, self.space)
        self.assertIsInstance(chart, Chart)
        self.assertEqual(chart.name, chart_name)

    def test_create_chart_with_streams(self):
        # Create the metric
        metric_name = 'my.metric'
        self.conn.submit(metric_name, 42, description='the desc for a metric')
        chart_name = "Typical chart"
        stream = Stream(metric=metric_name)
        chart = self.conn.create_chart(chart_name, self.space, streams=[stream.get_payload()])
        self.assertIsInstance(chart, Chart)

        self.assertEqual(chart.name, chart_name)
        self.assertEqual(len(chart.streams), 1)
        self.assertEqual(chart.streams[0].metric, metric_name)
        self.assertIsNone(chart.streams[0].composite)

    def test_chart_is_not_persisted(self):
        chart = Chart('not saved', self.space)
        self.assertFalse(chart.persisted())

    def test_rename_chart(self):
        chart = self.conn.create_chart('CPU', self.space)
        chart.rename('CPU 2')
        self.assertEqual(chart.name, 'CPU 2')

    def test_delete_chart(self):
        chart = self.conn.create_chart('cpu', self.space)
        self.conn.delete_chart(chart.id, self.space.id)
        self.assertEqual(len(self.conn.list_charts_in_space(self.space)), 0)

    def test_add_stream_to_chart(self):
        chart = self.conn.create_chart("Chart with no streams", self.space)
        metric_name = 'my.metric'
        self.conn.submit(metric_name, 42, description='metric description')
        chart.new_stream(metric_name)
        chart.save()
        self.assertEqual(len(chart.streams), 1)
        stream = chart.streams[0]
        self.assertEqual(stream.metric, metric_name)
        self.assertIsNone(stream.composite)

    def test_get_chart_from_space(self):
        chart = self.conn.create_chart('cpu', self.space)
        found = self.conn.get_chart(chart.id, self.space)
        self.assertEqual(found.id, chart.id)
        self.assertEqual(found.name, chart.name)

    def test_get_chart_from_space_id(self):
        chart = self.conn.create_chart('cpu', self.space)
        found = self.conn.get_chart(chart.id, self.space.id)
        self.assertEqual(found.id, chart.id)
        self.assertEqual(found.name, chart.name)


class TestChartModel(ChartsTest):
    def setUp(self):
        super(TestChartModel, self).setUp()
        self.space = self.conn.create_space('My Space')

    def test_init_with_connection(self):
        self.assertEqual(Chart(self.conn, 'cpu').connection, self.conn)

    def test_init_with_name(self):
        self.assertEqual(Chart(self.conn, 'cpu').name, 'cpu')

    def test_init_with_streams(self):
      s = [Stream('my.metric'), Stream('other.metric')]
      chart = Chart(self.conn, 'cpu', streams=s)
      self.assertEqual(chart.streams, s)

    def test_init_with_streams_dict(self):
      streams_dict = [
        {'metric': 'my.metric', 'source': 'blah', 'composite': None},
        {'metric': 'other.metric', 'source': '*', 'composite': None}
      ]
      chart = Chart(self.conn, 'cpu', streams=streams_dict)
      self.assertEqual(chart.streams[0].metric, streams_dict[0]['metric'])
      self.assertEqual(chart.streams[0].source, streams_dict[0]['source'])
      self.assertEqual(chart.streams[0].composite, streams_dict[0]['composite'])
      self.assertEqual(chart.streams[1].metric, streams_dict[1]['metric'])
      self.assertEqual(chart.streams[1].source, streams_dict[1]['source'])
      self.assertEqual(chart.streams[1].composite, streams_dict[1]['composite'])

    def test_init_with_streams_list(self):
      streams_list = [['my.metric', '*', None]]
      chart = Chart(self.conn, 'cpu', streams=streams_list)
      self.assertEqual(chart.streams[0].metric, streams_list[0][0])

    def test_save_chart(self):
        chart = Chart(self.conn, 'test', space_id=self.space.id)
        self.assertFalse(chart.persisted())
        self.assertIsNone(chart.id)
        chart.save()
        self.assertTrue(chart.persisted())
        self.assertIsNotNone(chart.id)

    def test_chart_is_persisted(self):
        chart = Chart(self.conn, 'test', id=42)
        self.assertTrue(chart.persisted())
        chart = Chart(self.conn, 'test', id=None)
        self.assertFalse(chart.persisted())

    def test_get_space_from_chart(self):
        chart = Chart(self.conn, 'CPU', space_id=self.space.id)
        space = chart.space()
        self.assertIsInstance(space, Space)
        self.assertEqual(space.id, self.space.id)

    def test_new_stream_defaults(self):
        chart = Chart(self.conn, 'test')
        self.assertEqual(len(chart.streams), 0)
        stream = chart.new_stream('my.metric')
        self.assertIsInstance(stream, Stream)
        self.assertEqual(stream.metric, 'my.metric')
        self.assertEqual(stream.source, '*')
        self.assertEqual(stream.composite, None)
        # Appends to chart streams
        self.assertEqual(len(chart.streams), 1)
        self.assertEqual(chart.streams[0].metric, 'my.metric')
        # Another way to do the same thing
        stream = chart.new_stream(metric='my.metric')
        self.assertEqual(stream.metric, 'my.metric')

    def test_new_stream_with_source(self):
        chart = Chart(self.conn, 'test')
        stream = chart.new_stream('my.metric', 'prod*')
        self.assertEqual(stream.metric, 'my.metric')
        self.assertEqual(stream.source, 'prod*')
        self.assertEqual(stream.composite, None)
        stream = chart.new_stream(metric='my.metric', source='prod*')
        self.assertEqual(stream.metric, 'my.metric')
        self.assertEqual(stream.source, 'prod*')
        self.assertEqual(stream.composite, None)

    def test_new_stream_with_composite(self):
        chart = Chart(self.conn, 'cpu')
        stream = chart.new_stream('my.metric')
        self.assertEqual(stream.metric, 'my.metric')
        self.assertEqual(stream.source, '*')
        self.assertEqual(stream.composite, None)

    def test_get_payload(self):
        chart = Chart(self.conn, 'cpu', type='bignumber', space_id=42)
        payload = chart.get_payload()
        self.assertEqual(payload['name'], chart.name)
        self.assertEqual(payload['type'], chart.type)
        self.assertEqual(payload['streams'], chart.streams)

    def test_streams_payload(self):
        streams_payload = [
          {'metric': 'some.metric', 'source': None, 'composite': None},
          {'metric': None, 'source': None, 'composite': 's("other.metric", "sf", {function: "sum"})'}
        ]
        chart = Chart(self.conn, 'cpu', streams=streams_payload)
        self.assertEqual(chart.streams_payload(), streams_payload)

    def test_get_payload_with_streams_dict(self):
        streams_payload = [
          {'metric': 'some.metric', 'source': None, 'composite': None},
          {'metric': 'another.metric', 'source': None, 'composite': None}
        ]
        chart = Chart(self.conn, 'cpu', type='bignumber', space_id=42, streams=streams_payload)
        chart_payload = chart.get_payload()
        self.assertEqual(chart_payload['streams'], streams_payload)

    def test_delete_chart(self):
        chart = self.conn.create_chart('cpu', self.space)
        chart.delete()
        self.assertEqual(self.space.charts(), [])




if __name__ == '__main__':
    unittest.main()
