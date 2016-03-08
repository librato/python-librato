import logging
import unittest
import librato
from librato.instruments import Stream
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
        assert len(spcs) == 0

    def test_create_space(self):
        name = "My_Space"
        spc = self.conn.create_space(name)
        assert type(spc) == librato.Space
        assert spc.name == name

        spcs = self.conn.list_spaces()
        assert len(spcs) == 1

    def test_get_space(self):
        name = "My_Space"
        self.conn.create_space(name)

        spcs = self.conn.list_spaces()
        assert len(spcs) == 1

        same_spc = self.conn.get_space(spcs[0].id)
        assert same_spc.id == 0
        assert same_spc.name == name

    def test_create_chart_without_streams_in_space(self):
        space_name = "My_Space"
        self.conn.create_space(space_name)

        spcs = self.conn.list_spaces()
        assert len(spcs) == 1

        spc = spcs[0]
        chrt_name = "My_Chart"
        chrt = self.conn.create_chart_in_space(chrt_name, spc)
        assert type(chrt) == librato.Chart

    def test_update_chart_with_streams_in_space(self):
        space_name = "My_Space"
        self.conn.create_space(space_name)

        spcs = self.conn.list_spaces()
        assert len(spcs) == 1

        spc = spcs[0]
        chrt_name = "My_Chart_with_Streams"
        chrt = self.conn.create_chart_in_space(chrt_name, spc)
        assert type(chrt) == librato.Chart
        assert chrt.name == chrt_name
        assert len(chrt.streams) == 0
        assert chrt.id == 0

        self.conn.submit('a_gauge', 12, description='the desc for a gauge')
        chrt.new_stream('a_gauge')
        self.conn.update_chart_in_space(chrt, spc)
        chrts = self.conn.list_charts_in_space(spc)
        assert len(chrts) == 1
        chrt = chrts[0]
        assert chrt.name == chrt_name
        assert len(chrt.streams) == 1
        assert chrt.id == 0
        assert chrt.streams[0].metric == "a_gauge"
        assert chrt.streams[0].composite == None

    def test_create_chart_with_streams_in_space(self):
        space_name = "My_Space"
        self.conn.create_space(space_name)

        spcs = self.conn.list_spaces()
        assert len(spcs) == 1

        spc = spcs[0]
        chrt_name = "My_Chart_created_with_Streams"
        self.conn.submit('a_gauge', 12, description='the desc for a gauge')
        stream = Stream(metric='a_gauge')
        chrt = self.conn.create_chart_in_space(chrt_name, spc, streams=[stream.get_payload()])
        assert type(chrt) == librato.Chart

        assert chrt.name == chrt_name
        assert len(chrt.streams) == 1
        assert chrt.id == 0
        assert chrt.streams[0].metric == "a_gauge"
        assert chrt.streams[0].composite == None

    def test_get_chart_from_space(self):
        space_name = "My_Space_with_Charts"
        self.conn.create_space(space_name)

        spcs = self.conn.list_spaces()
        assert len(spcs) == 1

        spc = spcs[0]
        chrt_name = "My_Chart"
        chrt = self.conn.create_chart_in_space(chrt_name, spc)
        assert type(chrt) == librato.Chart

        same_chrt1 = self.conn.get_chart_from_space(chrt.id, spc)
        assert same_chrt1.id == 0
        assert same_chrt1.name == chrt_name

        same_chrt2 = self.conn.get_chart_from_space_id(chrt.id, spc.id)
        assert same_chrt2.id == 0
        assert same_chrt2.name == chrt_name

    def test_update_space(self):
        name = "My_Space"
        spc = self.conn.create_space(name)
        assert type(spc) == librato.Space
        assert spc.name == name

        spcs = self.conn.list_spaces()
        assert len(spcs) == 1

        spc = spcs[0]
        assert spc.id == 0
        assert spc.name == name

        self.conn.update_space(spc, name="My_updated_Space")

        updated_spcs = self.conn.list_spaces()
        assert len(updated_spcs) == 1

        updated_spc = updated_spcs[0]
        assert spc.id == 0
        assert updated_spc.name == "My_updated_Space"

    def test_delete_chart_and_space(self):
        space_name = "My_Space"
        self.conn.create_space(space_name)

        spcs = self.conn.list_spaces()
        assert len(spcs) == 1

        spc = spcs[0]
        chrt_name = "My_Chart"
        chrt = self.conn.create_chart_in_space(chrt_name, spc)
        assert type(chrt) == librato.Chart

        chrts = self.conn.list_charts_in_space(spc)
        assert len(chrts) == 1

        chrt = chrts[0]
        self.conn.delete_chart_from_space(chrt.id, spc.id)

        deleted_chrts = self.conn.list_charts_in_space(spc)
        assert len(deleted_chrts) == 0

        self.conn.delete_space(spc.id)

        deleted_spcs = self.conn.list_spaces()
        assert len(deleted_spcs) == 0

if __name__ == '__main__':
    unittest.main()
