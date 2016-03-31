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
        self.assertEqual(len(self.conn.list_spaces()), 1)

    def test_list_spaces_when_none(self):
        spcs = self.conn.list_spaces()
        self.assertEqual(len(spcs), 0)

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

        updated_spaces = self.conn.list_spaces()
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
        self.assertEqual(len(self.conn.list_spaces()), 0)


class TestSpaceModel(SpacesTest):
    def setUp(self):
        super(TestSpaceModel, self).setUp()
        self.space = Space(self.conn, 'My Space')

    def test_connection(self):
        self.assertEqual(Space(self.conn, 'My Space').connection, self.conn)

    def test_init_with_name(self):
        self.assertEqual(Space(self.conn, 'My Space').name, 'My Space')

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

    def test_new_chart(self):
       chart = self.space.new_chart('test')
       self.assertIsInstance(chart, Chart)
       self.assertEqual(chart.name, 'test')
       self.assertEqual(chart.type, 'line')
       self.assertEqual(chart.persisted(), False)

    def test_new_chart_with_type(self):
       chart = self.space.new_chart('test', type='stacked')
       self.assertEqual(chart.type, 'stacked')
       chart = self.space.new_chart('test', type='bignumber')
       self.assertEqual(chart.type, 'bignumber')

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
