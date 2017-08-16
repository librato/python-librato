import logging
import unittest
import librato
from mock_connection import MockConnect, server

# Mock the server
librato.HTTPSConnection = MockConnect


class TestLibratoAlerts(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')
        self.name = 'my_alert'
        server.clean()

    def test_list_alerts_when_none(self):
        alerts = list(self.conn.list_alerts())
        self.assertEqual(len(alerts), 0)

    def test_create_alert_without_services_or_conditions(self):
        alert = self.conn.create_alert(self.name)
        self.assertIsInstance(alert, librato.Alert)
        self.assertEqual(alert.name, self.name)
        self.assertNotEqual(alert._id, 0)
        self.assertEqual(len(alert.services), 0)
        self.assertEqual(len(alert.conditions), 0)
        self.assertEqual(len(list(self.conn.list_alerts())), 1)

    def test_adding_an_alert_with_description(self):
        alert = self.conn.create_alert(self.name, description="test_description")
        self.assertEqual(alert.description, "test_description")

    def test_create_alert_with_conditions(self):
        cond = {'metric_name': 'cpu', 'type': 'above', 'threshold': 42}
        alert = self.conn.create_alert(self.name, conditions=[cond])
        self.assertEqual(len(alert.conditions), 1)
        self.assertEqual(alert.conditions[0].metric_name, 'cpu')
        self.assertEqual(alert.conditions[0].condition_type, 'above')
        self.assertEqual(alert.conditions[0].threshold, 42)

    def test_create_alert_with_add_condition(self):
        alert = self.conn.create_alert(self.name)
        alert.add_condition_for('cpu').above(200)
        self.assertEqual(len(alert.conditions), 1)
        self.assertEqual(alert.conditions[0].condition_type, 'above')
        self.assertEqual(alert.conditions[0].metric_name, 'cpu')
        self.assertEqual(alert.conditions[0].threshold, 200)

    def test_create_alert_with_condition_obj(self):
        c1 = librato.alerts.Condition('cpu', 'web*').above(42)
        c2 = librato.alerts.Condition('mem').below(99)
        alert = self.conn.create_alert(self.name, conditions=[c1, c2])
        self.assertEqual(len(alert.conditions), 2)
        self.assertEqual(alert.conditions[0].metric_name, 'cpu')
        self.assertEqual(alert.conditions[0].source, 'web*')
        self.assertEqual(alert.conditions[0].condition_type, 'above')
        self.assertEqual(alert.conditions[0].threshold, 42)
        self.assertEqual(alert.conditions[1].metric_name, 'mem')
        self.assertEqual(alert.conditions[1].source, '*')
        self.assertEqual(alert.conditions[1].condition_type, 'below')
        self.assertEqual(alert.conditions[1].threshold, 99)

    def test_deleting_an_alert(self):
        alert = self.conn.create_alert(self.name)
        # TODO: use requests directly instead of the client methods?
        assert len(list(self.conn.list_alerts())) == 1
        self.conn.delete_alert(self.name)
        assert len(list(self.conn.list_alerts())) == 0

    def test_deleting_an_inexistent_alert(self):
        self.conn.create_alert('say_my_name')
        self.conn.delete_alert('say_my_wrong_name')
        assert self.conn.get_alert('say_my_name') is not None

    def test_create_alert_with_service_id(self):
        alert = self.conn.create_alert(self.name)
        service_id = 1234
        alert.add_service(service_id)
        self.assertEqual(len(alert.services), 1)
        self.assertEqual(len(alert.conditions), 0)
        self.assertEqual(alert.services[0]._id, service_id)

    def test_create_alert_with_service_obj(self):
        service = librato.alerts.Service(1234)
        alert = self.conn.create_alert(self.name, services=[service])
        self.assertEqual(len(alert.services), 1)
        self.assertEqual(len(alert.conditions), 0)
        self.assertEqual(alert.services[0]._id, service._id)

    def test_add_above_condition(self):
        alert = self.conn.create_alert(self.name)
        alert.add_condition_for('metric_test').above(200, 'average').duration(5)
        assert len(alert.conditions) == 1
        condition = alert.conditions[0]
        assert condition.condition_type == 'above'
        assert condition.metric_name == 'metric_test'
        assert condition.threshold == 200
        assert condition._duration == 5

    def test_add_below_condition(self):
        alert = self.conn.create_alert(self.name)
        alert.add_condition_for('metric_test').below(200, 'average').duration(5)
        assert len(alert.conditions) == 1
        condition = alert.conditions[0]
        assert condition.condition_type == 'below'
        assert condition.metric_name == 'metric_test'
        assert condition.threshold == 200
        assert condition._duration == 5

    def test_add_absent_condition(self):
        alert = self.conn.create_alert(self.name)
        alert.add_condition_for('metric_test').stops_reporting_for(5)
        assert len(alert.conditions) == 1
        condition = alert.conditions[0]
        assert condition.condition_type == 'absent'
        assert condition.metric_name == 'metric_test'
        assert condition._duration == 5

    def test_immediate_condition(self):
        cond = librato.alerts.Condition('foo')

        cond._duration = None
        assert cond.immediate() is True

        # Not even sure this is a valid case, but testing anyway
        cond._duration = 0
        assert cond.immediate() is True

        cond._duration = 60
        assert cond.immediate() is False


class TestService(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')
        self.sample_payload = {
            'title': 'Email Ops',
            'type': 'mail',
            'settings': {'addresses': 'someone@example.com'}
        }
        server.clean()

    def test_list_services(self):
        services = list(self.conn.list_services())
        self.assertEqual(len(services), 0)
        # Hack this into the server until we have a :create_service
        # method on the actual connection
        server.create_service(self.sample_payload)
        # id is 1
        self.assertEqual(server.services[1], self.sample_payload)
        services = list(self.conn.list_services())
        self.assertEqual(len(services), 1)
        s = services[0]
        self.assertIsInstance(s, librato.alerts.Service)
        self.assertEqual(s.title, self.sample_payload['title'])
        self.assertEqual(s.type, self.sample_payload['type'])
        self.assertEqual(s.settings, self.sample_payload['settings'])

    def test_init_service(self):
        s = librato.alerts.Service(123, title='the title', type='mail',
                                   settings={'addresses': 'someone@example.com'})
        self.assertEqual(s._id, 123)
        self.assertEqual(s.title, 'the title')
        self.assertEqual(s.type, 'mail')
        self.assertEqual(s.settings['addresses'], 'someone@example.com')

    def test_service_from_dict(self):
        payload = {'id': 123, 'title': 'the title', 'type': 'slack',
                   'settings': {'room': 'a room'}}
        s = librato.alerts.Service.from_dict(self.conn, payload)
        self.assertEqual(s._id, 123)
        self.assertEqual(s.title, payload['title'])
        self.assertEqual(s.type, payload['type'])
        self.assertEqual(s.settings['room'], payload['settings']['room'])


if __name__ == '__main__':
    unittest.main()
