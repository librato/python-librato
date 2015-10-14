import logging
import unittest
import librato
from mock_connection import MockConnect, server

#logging.basicConfig(level=logging.DEBUG)
# Mock the server
librato.HTTPSConnection = MockConnect


class TestLibratoInstruments(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')
        server.clean()

    def test_list_instruments_when_none(self):
        ins = self.conn.list_instruments()
        assert len(ins) == 0

    def test_adding_a_new_instrument_without_streams(self):
        name = "my_INST"
        ins = self.conn.create_instrument(name)
        assert type(ins) == librato.Instrument
        assert ins.name == name
        assert len(ins.streams) == 0

    def test_adding_a_new_instrument_with_streams(self):
        name = "my_INST_with_STREAMS"
        ins = self.conn.create_instrument(name)
        assert type(ins) == librato.Instrument
        assert ins.name == name
        assert len(ins.streams) == 0
        assert ins.id == 1

        self.conn.submit('a_gauge', 12, description='the desc for a gauge')
        ins.new_stream('a_gauge')
        self.conn.update_instrument(ins)
        #list_ins = self.conn.list_instruments()
        assert ins.name == name
        assert len(ins.streams) == 1
        assert ins.id == 1
        assert ins.streams[0].metric == "a_gauge"
        assert ins.streams[0].composite == None

    def test_get_instrument(self):
        name = "my_INST_with_STREAMS"
        ins = self.conn.create_instrument(name)

        self.conn.submit('a_gauge', 12, description='the desc for a gauge')
        ins.new_stream('a_gauge')
        self.conn.update_instrument(ins)

        si = self.conn.get_instrument(ins.id)  # si ; same instrument
        assert type(si) == librato.Instrument
        assert si.name == name
        assert len(si.streams) == 1
        assert si.id == 1
        assert si.streams[0].metric == "a_gauge"
        assert si.streams[0].composite == None

    def test_adding_a_new_instrument_with_stream_properties(self):
        name = "my_INST_with_STREAMS"
        ins = self.conn.create_instrument(name)
        assert type(ins) == librato.Instrument
        assert ins.name == name
        assert len(ins.streams) == 0
        assert ins.id == 1

        ins.new_stream(composite='s("cpu", "*")', units_short='%', units_long='percentage',
                display_min=0, display_max=100, summary_function='average')
        self.conn.update_instrument(ins)
        ins = self.conn.get_instrument(1)
        assert ins.name == name
        assert len(ins.streams) == 1
        assert ins.id == 1
        assert ins.streams[0].composite == 's("cpu", "*")'
        assert ins.streams[0].units_short == '%'
        assert ins.streams[0].units_long == 'percentage'
        assert ins.streams[0].display_min == 0
        assert ins.streams[0].display_max == 100
        assert ins.streams[0].summary_function == 'average'

    def test_is_persisted(self):
        i = librato.Instrument(self.conn, 'test inst')
        assert i.is_persisted() == False
        i = librato.Instrument(self.conn, 'test inst', id=1234)
        assert i.is_persisted() == True

if __name__ == '__main__':
    unittest.main()
