import logging
import unittest
import librato
from librato import Space, Chart
from librato.streams import Stream
from mock_connection import MockConnect, server

# logging.basicConfig(level=logging.DEBUG)
# Mock the server
librato.HTTPSConnection = MockConnect


class SpacesTest(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')
        server.clean()


class TestSpacesConnection(SpacesTest):
    def test_list_spaces(self):
        self.conn.create_space('My Space')
        self.assertEqual(len(list(self.conn.list_spaces())), 1)

    def test_list_spaces_when_none(self):
        spcs = self.conn.list_spaces()
        self.assertEqual(len(list(spcs)), 0)

    # Find a space by ID
    def test_get_space(self):
        space = self.conn.create_space('My Space')
        found = self.conn.get_space(space.id)
        self.assertEqual(found.id, space.id)
        self.assertEqual(found.name, space.name)

    # Find a space by name
    def test_find_space(self):
        space = self.conn.create_space('My Space')
        found = self.conn.find_space(space.name)
        self.assertIsInstance(found, Space)
        self.assertEqual(found.name, space.name)

    def test_create_space(self):
        name = "My Space"
        space = self.conn.create_space(name)
        self.assertIsInstance(space, Space)
        self.assertEqual(space.name, name)

    def test_rename_space(self):
        name = 'My Space'
        new_name = 'My Space 42'
        space = self.conn.create_space(name)
        space.rename(new_name)
        found = self.conn.find_space(new_name)
        self.assertEqual(found.name, new_name)

    def test_list_charts(self):
        space_name = "My Space"
        space = self.conn.create_space(space_name)
        chart1 = self.conn.create_chart('CPU 1', space)
        chart2 = self.conn.create_chart('CPU 2', space)
        charts = space.charts()
        for c in charts:
            self.assertIsInstance(c, Chart)
            self.assertIn(c.name, ['CPU 1', 'CPU 2'])

    def test_update_space(self):
        space = self.conn.create_space('My Space')
        self.conn.update_space(space, name='New Name')

        updated_spaces = list(self.conn.list_spaces())
        self.assertEqual(len(updated_spaces), 1)

        updated = updated_spaces[0]
        updated = self.conn.get_space(space.id)
        self.assertEqual(updated.id, space.id)
        self.assertEqual(updated.name, 'New Name')

    def test_delete_chart(self):
        space = self.conn.create_space('My Space')
        chart = self.conn.create_chart('My Chart', space)
        self.conn.delete_chart(chart.id, space.id)
        self.assertEqual(len(self.conn.list_charts_in_space(space)), 0)

    def test_delete_space(self):
        space = self.conn.create_space('My Space')
        self.conn.delete_space(space.id)
        self.assertEqual(len(list(self.conn.list_spaces())), 0)


class TestSpaceModel(SpacesTest):
    def setUp(self):
        super(TestSpaceModel, self).setUp()
        self.space = Space(self.conn, 'My Space', id=123)

    def test_connection(self):
        self.assertEqual(Space(self.conn, 'My Space').connection, self.conn)

    def test_init_with_name(self):
        self.assertEqual(Space(self.conn, 'My Space').name, 'My Space')

    def test_init_with_tags(self):
        self.assertFalse(Space(self.conn, 'My Space').tags)
        self.assertFalse(Space(self.conn, 'My Space', tags=False).tags)
        self.assertTrue(Space(self.conn, 'My Space', tags=True).tags)

    def test_init_with_empty_name(self):
        self.assertEqual(Space(self.conn, None).name, None)

    def test_init_with_id(self):
        self.assertEqual(Space(self.conn, 'My Space', 123).id, 123)

    def test_charts_var(self):
        self.assertEqual(self.space._charts, None)

    def test_init_chart_ids_empty(self):
        self.assertEqual(self.space.chart_ids, [])

    def test_init_with_chart_payload(self):
        space = Space(self.conn, 'My Space', chart_dicts=[{'id': 123}, {'id': 456}])
        self.assertEqual(space.chart_ids, [123, 456])

    def test_space_is_not_persisted(self):
        space = Space(self.conn, 'not saved')
        self.assertFalse(space.persisted())

    def test_space_is_persisted_if_id_present(self):
        space = Space(self.conn, 'saved', id=42)
        self.assertTrue(space.persisted())

    # This only returns the name because that's all we can send to the Spaces API
    def test_get_payload(self):
        self.assertEqual(self.space.get_payload(), {'name': self.space.name})

    def test_from_dict(self):
        payload = {'id': 42, 'name': 'test', 'charts': [{'id': 123}, {'id': 456}]}
        space = Space.from_dict(self.conn, payload)
        self.assertIsInstance(space, Space)
        self.assertEqual(space.id, 42)
        self.assertEqual(space.name, 'test')
        self.assertEqual(space.chart_ids, [123, 456])

    def test_save_creates_space(self):
        space = Space(self.conn, 'not saved')
        self.assertFalse(space.persisted())
        resp = space.save()
        self.assertIsInstance(resp, Space)
        self.assertTrue(space.persisted())

    def save_updates_space(self):
        space = Space(self.conn, 'some name').save()
        self.assertEqual(space.name, 'some name')
        space.name = 'new name'
        space.save()
        self.assertEqual(self.conn.find_space('new_name').name, 'new name')

    def test_new_chart_name(self):
        chart = self.space.new_chart('test')
        self.assertIsInstance(chart, Chart)
        self.assertEqual(chart.name, 'test')

    def test_new_chart_not_persisted(self):
        # Doesn't save
        self.assertFalse(self.space.new_chart('test').persisted())

    def test_new_chart_type(self):
        chart = self.space.new_chart('test')
        self.assertEqual(chart.type, 'line')
        chart = self.space.new_chart('test', type='stacked')
        self.assertEqual(chart.type, 'stacked')
        chart = self.space.new_chart('test', type='bignumber')
        self.assertEqual(chart.type, 'bignumber')

    def test_new_chart_attrs(self):
        chart = self.space.new_chart('test',
                                     label='hello',
                                     min=-5,
                                     max=30,
                                     use_log_yaxis=True,
                                     use_last_value=True,
                                     related_space=1234)
        self.assertEqual(chart.label, 'hello')
        self.assertEqual(chart.min, -5)
        self.assertEqual(chart.max, 30)
        self.assertTrue(chart.use_log_yaxis)
        self.assertTrue(chart.use_last_value)
        self.assertEqual(chart.related_space, 1234)

    def test_new_chart_bignumber(self):
        chart = self.space.new_chart('test', type='bignumber',
                                     use_last_value=False)
        self.assertEqual(chart.type, 'bignumber')
        self.assertFalse(chart.use_last_value)

    def test_add_chart_name(self):
        space = self.conn.create_space('foo')
        chart = space.add_chart('bar')
        self.assertIsInstance(chart, Chart)
        self.assertEqual(chart.name, 'bar')

    def test_add_chart_type(self):
        space = self.conn.create_space('foo')
        chart = space.add_chart('baz', type='stacked')
        self.assertEqual(chart.type, 'stacked')

    def test_add_chart_persisted(self):
        space = self.conn.create_space('foo')
        chart = space.add_chart('bar')
        # Does save
        self.assertTrue(chart.persisted())

    def test_add_chart_streams(self):
        space = self.conn.create_space('foo')
        streams = [
            {'metric': 'my.metric', 'source': 'foo'},
            {'metric': 'my.metric2', 'source': 'bar'}
        ]
        chart = space.add_chart('cpu', streams=streams)
        self.assertEqual(chart.streams[0].metric, 'my.metric')
        self.assertEqual(chart.streams[0].source, 'foo')
        self.assertEqual(chart.streams[1].metric, 'my.metric2')
        self.assertEqual(chart.streams[1].source, 'bar')

    def test_add_chart_bignumber_default(self):
        space = self.conn.create_space('foo')
        chart = space.add_chart('baz', type='bignumber')
        self.assertEqual(chart.type, 'bignumber')
        # Leave this up to the Librato API to default
        self.assertIsNone(chart.use_last_value)

    def test_add_chart_bignumber_use_last_value(self):
        space = self.conn.create_space('foo')
        chart = space.add_chart('baz', type='bignumber', use_last_value=False)
        self.assertFalse(chart.use_last_value)
        chart = space.add_chart('baz', type='bignumber', use_last_value=True)
        self.assertTrue(chart.use_last_value)

    def test_add_line_chart(self):
        space = self.conn.create_space('foo')
        streams = [{'metric': 'my.metric', 'source': 'my.source'}]
        chart = space.add_line_chart('cpu', streams=streams)
        self.assertEqual([chart.name, chart.type], ['cpu', 'line'])
        self.assertEqual(len(chart.streams), 1)

    def test_add_single_line_chart_default(self):
        space = self.conn.create_space('foo')
        chart = space.add_single_line_chart('cpu', 'my.cpu.metric')
        self.assertEqual(chart.type, 'line')
        self.assertEqual(chart.name, 'cpu')
        self.assertEqual(len(chart.streams), 1)
        self.assertEqual(chart.streams[0].metric, 'my.cpu.metric')
        self.assertEqual(chart.streams[0].source, '*')

    def test_add_single_line_chart_source(self):
        space = self.conn.create_space('foo')
        chart = space.add_single_line_chart('cpu', 'my.cpu.metric', 'prod*')
        self.assertEqual(chart.streams[0].source, 'prod*')

    def test_add_single_line_chart_group_functions(self):
        space = self.conn.create_space('foo')
        chart = space.add_single_line_chart('cpu', 'my.cpu.metric', '*', 'min', 'max')
        stream = chart.streams[0]
        self.assertEqual(stream.group_function, 'min')
        self.assertEqual(stream.summary_function, 'max')

    def test_add_stacked_chart(self):
        space = self.conn.create_space('foo')
        streams = [{'metric': 'my.metric', 'source': 'my.source'}]
        chart = space.add_stacked_chart('cpu', streams=streams)
        self.assertEqual(chart.type, 'stacked')
        self.assertEqual([chart.name, chart.type], ['cpu', 'stacked'])
        self.assertEqual(len(chart.streams), 1)

    def test_add_single_stacked_chart(self):
        space = self.conn.create_space('foo')
        chart = space.add_single_stacked_chart('cpu', 'my.cpu.metric', '*')
        self.assertEqual(chart.type, 'stacked')
        self.assertEqual(chart.name, 'cpu')
        self.assertEqual(len(chart.streams), 1)
        self.assertEqual(chart.streams[0].metric, 'my.cpu.metric')
        self.assertEqual(chart.streams[0].source, '*')

    def test_add_bignumber_chart_default(self):
        space = self.conn.create_space('foo')
        chart = space.add_bignumber_chart('cpu', 'my.metric')
        self.assertEqual(chart.type, 'bignumber')
        self.assertEqual(chart.name, 'cpu')
        self.assertTrue(chart.use_last_value)
        stream = chart.streams[0]
        self.assertEqual(stream.metric, 'my.metric')
        self.assertEqual(stream.source, '*')
        self.assertEqual(stream.summary_function, 'average')

    def test_add_bignumber_chart_source(self):
        space = self.conn.create_space('foo')
        chart = space.add_bignumber_chart('cpu', 'my.metric', 'foo')
        self.assertEqual(chart.streams[0].source, 'foo')

    def test_add_bignumber_chart_summary_function(self):
        space = self.conn.create_space('foo')
        chart = space.add_bignumber_chart('cpu', 'my.metric',
                                          summary_function='min')
        self.assertEqual(chart.streams[0].summary_function, 'min')

    def test_add_bignumber_chart_group_function(self):
        space = self.conn.create_space('foo')
        chart = space.add_bignumber_chart('cpu', 'my.metric',
                                          group_function='max')
        self.assertEqual(chart.streams[0].group_function, 'max')

    def test_add_bignumber_chart_use_last_value(self):
        space = self.conn.create_space('foo')
        # True shows the most recent value, False reduces over time
        # Default to True
        chart = space.add_bignumber_chart('cpu', 'my.metric')
        self.assertTrue(chart.use_last_value)
        chart = space.add_bignumber_chart('cpu', 'my.metric', use_last_value=True)
        self.assertTrue(chart.use_last_value)
        chart = space.add_bignumber_chart('cpu', 'my.metric', use_last_value=False)
        self.assertFalse(chart.use_last_value)

    def test_delete_space(self):
        space = self.conn.create_space('Delete Me')
        # Ensure we can find it
        self.assertEqual(self.conn.find_space(space.name).name, space.name)
        resp = space.delete()
        # Returns None
        self.assertIsNone(resp)
        # Ensure it was deleted
        self.assertIsNone(self.conn.find_space(space.name))


if __name__ == '__main__':
    unittest.main()
