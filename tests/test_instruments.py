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
        ins.new_stream('a_gauge', source='a_source')
        self.conn.update_instrument(ins)
        #list_ins = self.conn.list_instruments()
        assert ins.name == name
        assert len(ins.streams) == 1
        assert ins.id == 1
        assert ins.streams[0].metric == 'a_gauge'
        assert ins.streams[0].source == 'a_source'
        assert ins.streams[0].composite == None

    def test_get_instrument(self):
        name = "my_INST_with_STREAMS"
        ins = self.conn.create_instrument(name)

        self.conn.submit('a_gauge', 12, description='the desc for a gauge')
        ins.new_stream('a_gauge', color='#52D74C')
        self.conn.update_instrument(ins)

        si = self.conn.get_instrument(ins.id)  # si ; same instrument
        assert type(si) == librato.Instrument
        assert si.name == name
        assert len(si.streams) == 1
        assert si.id == 1
        assert si.streams[0].metric == 'a_gauge'
        assert si.streams[0].composite == None
        assert si.streams[0].color == '#52D74C'

    def test_adding_a_new_instrument_with_composite_stream_properties(self):
        name = "my_INST_with_STREAMS"
        ins = self.conn.create_instrument(name)
        assert type(ins) == librato.Instrument
        assert ins.name == name
        assert len(ins.streams) == 0
        assert ins.id == 1

        ins.new_stream(composite='s("cpu", "*")', name='CPU',
                units_short='%', units_long='percentage',
                display_min=0, display_max=100, summary_function='average',
                transform_function='x/1', period=60, color='#52D74C')
        self.conn.update_instrument(ins)
        ins = self.conn.get_instrument(1)
        assert ins.name == name
        assert len(ins.streams) == 1
        assert ins.id == 1
        assert ins.streams[0].composite == 's("cpu", "*")'
        assert ins.streams[0].name == 'CPU'
        assert ins.streams[0].units_short == '%'
        assert ins.streams[0].units_long == 'percentage'
        assert ins.streams[0].display_min == 0
        assert ins.streams[0].display_max == 100
        assert ins.streams[0].summary_function == 'average'
        assert ins.streams[0].transform_function == 'x/1'
        assert ins.streams[0].period == 60
        assert ins.streams[0].color == '#52D74C'

    def test_adding_a_new_instrument_with_metric_stream_properties(self):
        name = "my_INST_with_STREAMS"
        ins = self.conn.create_instrument(name)
        assert type(ins) == librato.Instrument
        assert ins.name == name
        assert len(ins.streams) == 0
        assert ins.id == 1

        ins.new_stream(metric='cpu', name='CPU', source='*',
                units_short='%', units_long='percentage',
                display_min=0, display_max=100, summary_function='average',
                transform_function='x/1', period=60,
                group_function='average', color='#52D74C')
        self.conn.update_instrument(ins)
        ins = self.conn.get_instrument(1)
        assert ins.name == name
        assert len(ins.streams) == 1
        assert ins.id == 1
        assert ins.streams[0].metric == 'cpu'
        assert ins.streams[0].name == 'CPU'
        assert ins.streams[0].source == '*'
        assert ins.streams[0].units_short == '%'
        assert ins.streams[0].units_long == 'percentage'
        assert ins.streams[0].display_min == 0
        assert ins.streams[0].display_max == 100
        assert ins.streams[0].summary_function == 'average'
        assert ins.streams[0].transform_function == 'x/1'
        assert ins.streams[0].period == 60
        assert ins.streams[0].group_function == 'average'
        assert ins.streams[0].color == '#52D74C'

    def test_adding_a_new_instrument_omits_composite_conflicting_properties(self):
        name = "my_INST_with_STREAMS"
        ins = self.conn.create_instrument(name)
        assert type(ins) == librato.Instrument
        assert ins.name == name
        assert len(ins.streams) == 0
        assert ins.id == 1

        ins.new_stream(composite='s("cpu", "*")', name='CPU',
                metric='cpu', source='*', group_function='average')
        self.conn.update_instrument(ins)
        ins = self.conn.get_instrument(1)
        assert ins.name == name
        assert len(ins.streams) == 1
        assert ins.id == 1
        assert ins.streams[0].composite == 's("cpu", "*")'
        assert ins.streams[0].metric == None
        assert ins.streams[0].source == None
        assert ins.streams[0].group_function == None

    def test_is_persisted(self):
        i = librato.Instrument(self.conn, 'test inst')
        assert i.is_persisted() == False
        i = librato.Instrument(self.conn, 'test inst', id=1234)
        assert i.is_persisted() == True

if __name__ == '__main__':
    unittest.main()
