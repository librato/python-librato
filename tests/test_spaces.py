import logging
import unittest
import librato
from librato.streams import Stream
from mock_connection import MockConnect, server

# logging.basicConfig(level=logging.DEBUG)
# Mock the server
librato.HTTPSConnection = MockConnect


class TestLibratoSpace(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')
        server.clean()

    def test_list_when_none(self):
        spcs = self.conn.list_spaces()
        self.assertEqual(len(spcs), 0)

    def test_create_space(self):
        name = "My Space"
        spc = self.conn.create_space(name)
        self.assertIsInstance(spc, librato.Space)
        self.assertEqual(spc.name, name)

        spcs = self.conn.list_spaces()
        self.assertEqual(len(spcs), 1)

    # Find a space by ID
    def test_get_space(self):
        name = "My Space"
        self.conn.create_space(name)

        spcs = self.conn.list_spaces()
        self.assertEqual(len(spcs), 1)

        same_spc = self.conn.get_space(spcs[0].id)
        self.assertEqual(same_spc.id, 0)
        self.assertEqual(same_spc.name, name)

    # Find a space by name
    def test_find_space(self):
        name = 'My Space'
        self.conn.create_space(name)
        space = self.conn.find_space(name)
        self.assertIsInstance(space, librato.Space)
        self.assertEqual(space.name, name)

    def test_rename_space(self):
        name = 'My Space'
        new_name = 'My Space 42'
        space = self.conn.create_space(name)
        space.rename(new_name)
        self.assertEqual(self.conn.find_space(new_name).name, new_name)

    def test_get_chart_from_space(self):
        space_name = "My Space with Charts"
        self.conn.create_space(space_name)

        spcs = self.conn.list_spaces()
        self.assertEqual(len(spcs), 1)

        spc = spcs[0]
        chrt_name = "My Chart"
        chrt = self.conn.create_chart(chrt_name, spc)
        self.assertIsInstance(chrt, librato.Chart)

        same_chrt1 = self.conn.get_chart(chrt.id, spc)
        self.assertEqual(same_chrt1.id, 0)
        self.assertEqual(same_chrt1.name, chrt_name)

        same_chrt2 = self.conn.get_chart(chrt.id, spc.id)
        self.assertEqual(same_chrt1.id, 0)
        self.assertEqual(same_chrt1.name, chrt_name)
        self.assertEqual(same_chrt2.id, 0)
        self.assertEqual(same_chrt2.name, chrt_name)

    def test_update_space(self):
        name = "My Space"
        spc = self.conn.create_space(name)
        self.assertIsInstance(spc, librato.Space)
        self.assertEqual(spc.name, name)

        spcs = self.conn.list_spaces()
        self.assertEqual(len(spcs), 1)

        spc = spcs[0]
        self.assertEqual(spc.id, 0)
        self.assertEqual(spc.name, name)

        self.conn.update_space(spc, name="My_updated_Space")

        updated_spcs = self.conn.list_spaces()
        self.assertEqual(len(updated_spcs), 1)

        updated_spc = updated_spcs[0]
        self.assertEqual(updated_spc.id, 0)
        self.assertEqual(updated_spc.name, "My_updated_Space")

    def test_delete_chart_and_space(self):
        space_name = "My Space"
        self.conn.create_space(space_name)

        spcs = self.conn.list_spaces()
        self.assertEqual(len(spcs), 1)

        spc = spcs[0]
        chrt_name = "My Chart"
        chrt = self.conn.create_chart(chrt_name, spc)
        self.assertIsInstance(chrt, librato.Chart)

        chrts = self.conn.list_charts_in_space(spc)
        self.assertEqual(len(chrts), 1)

        chrt = chrts[0]
        self.conn.delete_chart(chrt.id, spc.id)

        deleted_chrts = self.conn.list_charts_in_space(spc)
        self.assertEqual(len(deleted_chrts), 0)

        self.conn.delete_space(spc.id)

        deleted_spcs = self.conn.list_spaces()
        self.assertEqual(len(deleted_spcs), 0)


class TestLibratoChart(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')
        server.clean()
        self.space = self.conn.create_space("My Space")

    def test_connection(self):
        self.assertEqual(librato.Chart(self.conn, 'My Chart').connection, self.conn)

    def test_chart_name(self):
        self.assertEqual(librato.Chart(self.conn, 'My Chart').name, 'My Chart')

    def test_space_id(self):
        self.assertEqual(librato.Chart(self.conn, 'My Chart', space_id=42).space_id, 42)

    def test_space_attribute(self):
        chart = librato.Chart(self.conn, 'My Chart')
        chart._space = self.space
        self.assertEqual(chart._space, self.space)

    def test_chart_type(self):
        # Debated `chart_type` vs `type`, going with `type`
        self.assertEqual(librato.Chart(self.conn, 'My Chart', type='line').type, 'line')
        self.assertEqual(librato.Chart(self.conn, 'My Chart', type='stacked').type, 'stacked')
        self.assertEqual(librato.Chart(self.conn, 'My Chart', type='bignumber').type, 'bignumber')

    def test_create_chart_without_streams(self):
        chart_name = "Empty Chart"
        chart = self.conn.create_chart(chart_name, self.space)
        self.assertIsInstance(chart, librato.Chart)
        self.assertEqual(chart.name, chart_name)

    def test_create_chart_with_streams(self):
        # Create the metric
        metric_name = 'my.metric'
        self.conn.submit(metric_name, 42, description='the desc for a metric')
        chart_name = "Typical chart"
        stream = Stream(metric=metric_name)
        chart = self.conn.create_chart(chart_name, self.space, streams=[stream.get_payload()])
        self.assertIsInstance(chart, librato.Chart)

        self.assertEqual(chart.name, chart_name)
        self.assertEqual(len(chart.streams), 1)
        self.assertEqual(chart.streams[0].metric, metric_name)
        self.assertIsNone(chart.streams[0].composite)

    def test_save_chart(self):
        chart = self.conn.create_chart('CPU', self.space)
        chart.save()
        self.assertEqual(chart.space_id, self.space.id)

    def test_chart_is_persisted(self):
        chart = self.conn.create_chart('CPU', self.space)
        self.assertTrue(chart.persisted())

    def test_chart_is_not_persisted(self):
        chart = librato.Chart('not saved', self.space)
        self.assertFalse(chart.persisted())

    def test_rename_chart(self):
        chart = self.conn.create_chart('CPU', self.space)
        chart.rename('CPU 2')
        self.assertEqual(chart.name, 'CPU 2')

    def test_get_space_from_chart(self):
        chart = self.conn.create_chart('CPU', self.space)
        self.assertEqual(chart.space().id, self.space.id)

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


if __name__ == '__main__':
    unittest.main()
