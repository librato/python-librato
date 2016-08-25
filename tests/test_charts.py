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

    def test_create_chart(self):
        # Create a couple of metrics
        self.conn.submit('my.metric', 42)
        self.conn.submit('my.metric2', 43)
        # Create charts in the space
        chart_name = "Typical chart"
        chart = self.conn.create_chart(
            chart_name,
            self.space,
            streams=[
                {'metric': 'my.metric', 'source': '*', 'summary_function': 'max'},
                {'metric': 'my.metric2', 'source': 'foo', 'color': '#FFFFFF'}
            ]
        )
        self.assertIsInstance(chart, Chart)
        self.assertIsNotNone(chart.id)
        self.assertEqual(chart.space_id, self.space.id)
        self.assertEqual(chart.name, chart_name)
        self.assertEqual(chart.streams[0].metric, 'my.metric')
        self.assertEqual(chart.streams[0].source, '*')
        self.assertEqual(chart.streams[0].summary_function, 'max')
        self.assertEqual(chart.streams[1].metric, 'my.metric2')
        self.assertEqual(chart.streams[1].source, 'foo')
        self.assertEqual(chart.streams[1].color, '#FFFFFF')

    def test_create_chart_without_streams(self):
        chart_name = "Empty Chart"
        chart = self.conn.create_chart(chart_name, self.space)
        self.assertIsInstance(chart, Chart)
        self.assertEqual(chart.name, chart_name)
        # Line by default
        self.assertEqual(chart.type, 'line')
        self.assertEqual(len(chart.streams), 0)

    def test_rename_chart(self):
        chart = self.conn.create_chart('CPU', self.space)
        chart.rename('CPU 2')
        self.assertEqual(chart.name, 'CPU 2')
        self.assertEqual(self.conn.get_chart(chart.id, self.space).name, 'CPU 2')

    def test_delete_chart(self):
        chart = self.conn.create_chart('cpu', self.space)
        self.conn.delete_chart(chart.id, self.space.id)
        self.assertEqual(len(self.conn.list_charts_in_space(self.space)), 0)

    def test_add_stream_to_chart(self):
        chart = self.conn.create_chart("Chart with no streams", self.space)
        metric_name = 'my.metric'
        self.conn.submit(metric_name, 42, description='metric description')
        chart.new_stream(metric=metric_name)
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

    def test_find_chart_by_name(self):
        chart = self.conn.create_chart('cpu', self.space)
        found = self.conn.find_chart('cpu', self.space)
        self.assertEqual(found.name, 'cpu')


class TestChartModel(ChartsTest):
    def setUp(self):
        super(TestChartModel, self).setUp()
        self.space = self.conn.create_space('My Space')

    def test_init_connection(self):
        self.assertEqual(Chart(self.conn).connection, self.conn)

    def test_init_name(self):
        self.assertIsNone(Chart(self.conn).name)
        self.assertEqual(Chart(self.conn, 'cpu').name, 'cpu')

    def test_init_chart_type(self):
        # Debated `chart_type` vs `type`, going with `type`
        self.assertEqual(Chart(self.conn, type='line').type, 'line')
        self.assertEqual(Chart(self.conn, type='stacked').type, 'stacked')
        self.assertEqual(Chart(self.conn, type='bignumber').type, 'bignumber')

    def test_init_space_id(self):
        self.assertEqual(Chart(self.conn, space_id=42).space_id, 42)

    def test_space_attribute(self):
        chart = Chart(self.conn)
        chart._space = self.space
        self.assertEqual(chart._space, self.space)

    def test_init_streams(self):
        self.assertEqual(Chart(self.conn).streams, [])

        s = [Stream('my.metric'), Stream('other.metric')]
        chart = Chart(self.conn, streams=s)
        self.assertEqual(chart.streams, s)

    def test_init_streams_dict(self):
        streams_dict = [
            {'metric': 'my.metric', 'source': 'blah', 'composite': None},
            {'metric': 'other.metric', 'source': '*', 'composite': None}
        ]
        chart = Chart(self.conn, streams=streams_dict)
        self.assertEqual(chart.streams[0].metric, streams_dict[0]['metric'])
        self.assertEqual(chart.streams[0].source, streams_dict[0]['source'])
        self.assertEqual(chart.streams[0].composite, streams_dict[0]['composite'])
        self.assertEqual(chart.streams[1].metric, streams_dict[1]['metric'])
        self.assertEqual(chart.streams[1].source, streams_dict[1]['source'])
        self.assertEqual(chart.streams[1].composite, streams_dict[1]['composite'])

    def test_init_streams_list(self):
        streams_list = [['my.metric', '*', None]]
        chart = Chart(self.conn, streams=streams_list)
        self.assertEqual(chart.streams[0].metric, streams_list[0][0])

    def test_init_streams_group_functions(self):
        streams_dict = [
            {'metric': 'my.metric', 'source': '*',
             'group_function': 'sum', 'summary_function': 'max'}
        ]
        chart = Chart(self.conn, streams=streams_dict)
        stream = chart.streams[0]
        self.assertEqual(stream.group_function, 'sum')
        self.assertEqual(stream.summary_function, 'max')

    def test_init_min_max(self):
        chart = Chart(self.conn, min=-42, max=100)
        self.assertEqual(chart.min, -42)
        self.assertEqual(chart.max, 100)

    def test_init_label(self):
        chart = Chart(self.conn, label='I heart charts')
        self.assertEqual(chart.label, 'I heart charts')

    def test_init_use_log_yaxis(self):
        chart = Chart(self.conn, use_log_yaxis=True)
        self.assertTrue(chart.use_log_yaxis)

    def test_save_chart(self):
        chart = Chart(self.conn, 'test', space_id=self.space.id)
        self.assertFalse(chart.persisted())
        self.assertIsNone(chart.id)
        resp = chart.save()
        self.assertIsInstance(resp, Chart)
        self.assertTrue(chart.persisted())
        self.assertIsNotNone(chart.id)
        self.assertEqual(chart.type, 'line')

    def test_save_persists_type(self):
        # Ensure that type gets passed in the payload
        for t in ['stacked', 'bignumber']:
            chart = Chart(self.conn, space_id=self.space.id, type=t)
            chart.save()
            found = self.conn.get_chart(chart.id, self.space.id)
            self.assertEqual(found.type, t)

    def test_save_persists_min_max(self):
        chart = Chart(self.conn, space_id=self.space.id)
        self.assertIsNone(chart.min)
        self.assertIsNone(chart.max)
        chart.min = 5
        chart.max = 30
        chart.save()
        found = self.conn.get_chart(chart.id, self.space.id)
        self.assertEqual(found.min, 5)
        self.assertEqual(found.max, 30)

    def test_save_persists_label(self):
        chart = Chart(self.conn, space_id=self.space.id)
        self.assertIsNone(chart.label)
        chart.label = 'my label'
        chart.save()
        found = self.conn.get_chart(chart.id, self.space.id)
        self.assertEqual(found.label, 'my label')

    def test_save_persists_log_y_axis(self):
        chart = Chart(self.conn, space_id=self.space.id)
        self.assertIsNone(chart.use_log_yaxis)
        chart.use_log_yaxis = True
        chart.save()
        found = self.conn.get_chart(chart.id, self.space.id)
        self.assertTrue(found.use_log_yaxis)

    def test_save_persists_use_last_value(self):
        chart = Chart(self.conn, space_id=self.space.id)
        self.assertIsNone(chart.use_last_value)
        chart.use_last_value = True
        chart.save()
        found = self.conn.get_chart(chart.id, self.space.id)
        self.assertTrue(found.use_last_value)

    def test_save_persists_related_space(self):
        chart = Chart(self.conn, space_id=self.space.id)
        self.assertIsNone(chart.related_space)
        chart.related_space = 1234
        chart.save()
        found = self.conn.get_chart(chart.id, self.space.id)
        self.assertTrue(found.related_space)

    def test_chart_is_not_persisted(self):
        chart = Chart('not saved', self.space)
        self.assertFalse(chart.persisted())

    def test_chart_is_persisted_if_id_present(self):
        chart = Chart(self.conn, 'test', id=42)
        self.assertTrue(chart.persisted())
        chart = Chart(self.conn, 'test', id=None)
        self.assertFalse(chart.persisted())

    def test_get_space_from_chart(self):
        chart = Chart(self.conn, space_id=self.space.id)
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
        chart = Chart(self.conn)
        composite_formula = 's("my.metric", "*")'
        stream = chart.new_stream(composite=composite_formula)
        self.assertIsNone(stream.metric)
        self.assertIsNone(stream.source)
        self.assertEqual(stream.composite, composite_formula)

    def test_get_payload(self):
        chart = Chart(self.conn)
        payload = chart.get_payload()
        self.assertEqual(payload['name'], chart.name)
        self.assertEqual(payload['type'], chart.type)
        self.assertEqual(payload['streams'], chart.streams)

    def test_get_payload_bignumber(self):
        streams = [{'metric': 'my.metric', 'source': '*'}]
        chart = Chart(self.conn, type='bignumber', streams=streams,
                      use_last_value=False)
        payload = chart.get_payload()
        self.assertEqual(payload['name'], chart.name)
        self.assertEqual(payload['type'], chart.type)
        self.assertEqual(payload['streams'], streams)
        self.assertEqual(payload['use_last_value'], chart.use_last_value)

    def test_streams_payload(self):
        streams_payload = [
            {'metric': 'some.metric', 'source': None, 'composite': None},
            {'metric': None, 'source': None, 'composite': 's("other.metric", "sf", {function: "sum"})'}
        ]
        chart = Chart(self.conn, streams=streams_payload)
        self.assertEqual(chart.streams_payload()[0]['metric'], streams_payload[0]['metric'])

    def test_get_payload_with_streams_dict(self):
        streams_payload = [
            {'metric': 'some.metric', 'source': None, 'composite': None},
            {'metric': 'another.metric', 'source': None, 'composite': None}
        ]
        chart = Chart(self.conn, type='bignumber', space_id=42, streams=streams_payload)
        chart_payload = chart.get_payload()
        self.assertEqual(chart_payload['streams'][0]['metric'], streams_payload[0]['metric'])
        self.assertEqual(chart_payload['streams'][1]['metric'], streams_payload[1]['metric'])

    def test_delete_chart(self):
        chart = self.conn.create_chart('cpu', self.space)
        chart.delete()
        self.assertEqual(self.space.charts(), [])


if __name__ == '__main__':
    unittest.main()
