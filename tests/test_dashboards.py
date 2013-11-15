import logging
import unittest
import librato
from mock_connection import MockConnect, server

#logging.basicConfig(level=logging.DEBUG)
# Mock the server
librato.HTTPSConnection = MockConnect


class TestLibratoDashboard(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')
        server.clean()

    def test_list_when_none(self):
        dbs = self.conn.list_dashboards()
        assert len(dbs) == 0

    def test_create(self):
        name = "My_DashBoard"
        db = self.conn.create_dashboard(name)
        assert type(db) == librato.Dashboard
        assert db.name == name

        ins = self.conn.list_dashboards()
        assert len(ins) == 1

    def test_get_dashboard(self):
        name = "My_DashBoard"
        self.conn.create_dashboard(name)

        dbs = self.conn.list_dashboards()
        assert len(dbs) == 1

        same_db = self.conn.get_dashboard(dbs[0].id)
        assert same_db.id == 0
        assert same_db.name == name

    def test_create_with_instrument(self):
        name = "My_DashBoard"
        db = self.conn.create_dashboard(name)
        assert type(db) == librato.Dashboard
        assert db.name == name
        assert db.id == 0
        assert len(db.get_instruments()) == 0

        i_name = "my_INST"
        ins = self.conn.create_instrument(i_name)
        assert type(ins) == librato.Instrument
        assert ins.name == i_name
        assert len(ins.streams) == 0
        db.instrument_ids.append({"id": ins.id})
        db.save()  # call update_dashboard

        same_db = self.conn.get_dashboard(db.id)
        assert same_db.id == 0
        assert same_db.name == name
        assert len(same_db.instrument_ids) == 1
        a_ins = same_db.get_instruments()
        assert len(a_ins) == 1
        assert a_ins[0].name == i_name


if __name__ == '__main__':
    unittest.main()
