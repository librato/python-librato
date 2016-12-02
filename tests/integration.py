# Copyright (c) 2012 Chris Moyer http://coredumped.org
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import logging
from contextlib import contextmanager
import nose
import unittest
from librato.exceptions import BadRequest
import librato
import os
from random import randint
import time
logging.basicConfig(level=logging.INFO)


class TestLibratoBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """ Auth """
        user = os.environ.get('LIBRATO_USER')
        token = os.environ.get('LIBRATO_TOKEN')
        assert user and token, "Must set LIBRATO_USER and LIBRATO_TOKEN to run tests"
        print "%s and %s" % (user, token)

        """ Ensure user really wants to run these tests """
        are_you_sure = os.environ.get('LIBRATO_ALLOW_INTEGRATION_TESTS')
        assert are_you_sure == 'Y', "INTEGRATION TESTS WILL DELETE METRICS " \
            "IN YOUR ACCOUNT!!! " \
            "If you are absolutely sure that you want to run tests "\
            "against %s, please set LIBRATO_ALLOW_INTEGRATION_TESTS "\
            "to 'Y'" % user

        """Initialize the Librato Connection"""
        cls.conn = librato.connect(user, token)
        cls.conn_sanitize = librato.connect(user, token, sanitizer=librato.sanitize_metric_name)

    # Since these are live tests, I'm adding this to account for the slight
    # delay in RDS replication lag at the API (if needed).
    # Otherwise we get semi-random failures.
    def wait_for_replication(self):
        time.sleep(1)


class TestLibratoBasic(TestLibratoBase):

    def test_list_metrics(self):
        metrics = self.conn.list_metrics()

    def _add_and_verify_metric(self, name, value, desc, connection=None, type='gauge'):
        if not connection:
            connection = self.conn
        connection.submit(name, value, type=type, description=desc)
        self.wait_for_replication()
        metric = connection.get(name)
        assert metric and metric.name == connection.sanitize(name)
        assert metric.description == desc
        return metric

    def _delete_and_verify_metric(self, names, connection=None):
        if not connection:
            connection = self.conn
        connection.delete(names)
        time.sleep(2)
        # Make sure it's not there anymore
        try:
            metric = connection.get(names)
        except:
            metric = None
        assert(metric is None)

    def test_long_sanitized_metric(self):
        name, desc = 'a' * 256, 'Too long, will error'
        with self.assertRaises(BadRequest):
            self._add_and_verify_metric(name, 10, desc, self.conn)
        self._add_and_verify_metric(name, 10, desc, self.conn_sanitize)
        self._delete_and_verify_metric(name, self.conn_sanitize)

    def test_invalid_sanitized_metric(self):
        name, desc = r'I AM #*@#@983221 CRazy((\\\\] invalid', 'Crazy invalid'
        with self.assertRaises(BadRequest):
            self._add_and_verify_metric(name, 10, desc, self.conn)
        self._add_and_verify_metric(name, 10, desc, self.conn_sanitize)
        self._delete_and_verify_metric(name, self.conn_sanitize)

    def test_create_and_delete_gauge(self):
        name, desc = 'Test', 'Test Gauge to be removed'
        self._add_and_verify_metric(name, 10, desc)
        self._delete_and_verify_metric(name)

    def test_create_and_delete_counter(self):
        name, desc = 'Test_counter', 'Test Counter to be removed'
        self._add_and_verify_metric(name, 10, desc, type='counter')
        self._delete_and_verify_metric(name)

    def test_batch_delete(self):
        name_one, desc_one = 'Test_one', 'Test gauge to be removed'
        name_two, desc_two = 'Test_two', 'Test counter to be removed'
        self._add_and_verify_metric(name_one, 10, desc_one)
        self._add_and_verify_metric(name_two, 10, desc_two, type='counter')
        self._delete_and_verify_metric([name_one, name_two])

    def test_save_gauge_metrics(self):
        name, desc = 'Test', 'Test Counter to be removed'
        self.conn.submit(name, 10, description=desc)
        self.conn.submit(name, 20, description=desc)
        self.conn.delete(name)

    def test_send_batch_gauge_measurements(self):
        q = self.conn.new_queue()
        for t in range(1, 10):
            q.add('temperature', randint(20, 40))
        q.submit()

        for t in range(1, 10):
            q.add('temperature', randint(20, 40), measure_time=time.time() + t)
        q.submit()

        for t in range(1, 10):
            q.add('temperature', randint(20, 40), source='upstairs', measure_time=time.time() + t)
        q.submit()

        for t in range(1, 50):
            q.add('temperature', randint(20, 30), source='downstairs', measure_time=time.time() + t)
        q.submit()
        self.conn.delete('temperature')

    def test_batch_sanitation(self):
        name_one, name_two = 'a' * 500, r'DSJAK#32102391S,m][][[{{]\\'

        def run_batch(connection):
            q = connection.new_queue()
            q.add(name_one, 10)
            q.add(name_two, 10)
            q.submit()

        with self.assertRaises(BadRequest):
            run_batch(self.conn)
        run_batch(self.conn_sanitize)

        self.conn_sanitize.delete([name_one, name_two])

    def test_submit_empty_queue(self):
        self.conn.new_queue().submit()

    def test_send_batch_counter_measurements(self):
        q = self.conn.new_queue()
        for nr in range(1, 2):
            q.add('num_req', nr, type='counter', source='server1', measure_time=time.time() - 1)
            q.add('num_req', nr, type='counter', source='server2', measure_time=time.time() - 1)
        q.submit()

    def test_update_metrics_attributes(self):
        name, desc = 'Test', 'A great gauge.'
        self.conn.submit(name, 10, description=desc)
        self.wait_for_replication()
        gauge = self.conn.get(name)
        assert gauge and gauge.name == name
        assert gauge.description == desc

        gauge = self.conn.get(name)
        attrs = gauge.attributes
        attrs['display_min'] = 0
        self.conn.update(name, attributes=attrs)

        gauge = self.conn.get(name)
        assert gauge.attributes['display_min'] == 0

        self.conn.delete(name)

    def test_sanitized_update(self):
        name, desc = 'a' * 1000, 'too long, really'
        new_desc = 'different'
        self.conn_sanitize.submit(name, 10, description=desc)
        gauge = self.conn_sanitize.get(name)
        assert gauge.description == desc

        attrs = gauge.attributes['description'] = new_desc
        with self.assertRaises(BadRequest):
            self.conn.update(name, attributes=attrs)
        self.conn_sanitize.delete(name)


class TestLibratoAlertsIntegration(TestLibratoBase):

    alerts_created_during_test = []
    gauges_used_during_test = ['metric_test', 'cpu']

    def setUp(self):
        # Ensure metric names exist so we can create conditions on them
        for m in self.gauges_used_during_test:
            # Create or just update a gauge metric
            self.conn.submit(m, 42)

    def tearDown(self):
        for name in self.alerts_created_during_test:
            self.conn.delete_alert(name)

    def test_add_empty_alert(self):
        name = self.unique_name("test_add_empty_alert")
        alert = self.conn.create_alert(name)
        alert_id = alert._id
        alert = self.conn.get_alert(name)
        assert alert._id == alert_id
        assert alert.name == alert.name
        assert len(alert.conditions) == 0
        assert len(alert.services) == 0

    def test_inactive_alert_with_rearm_seconds(self):
        name = self.unique_name("test_inactive_alert_with_rearm_seconds")
        alert = self.conn.create_alert(name, active=False, rearm_seconds=1200)
        alert_id = alert._id
        alert = self.conn.get_alert(name)
        assert alert.rearm_seconds == 1200
        assert alert.active is False

    def test_add_alert_with_a_condition(self):
        name = self.unique_name("test_add_alert_with_a_condition")
        alert = self.conn.create_alert(name)
        alert.add_condition_for('metric_test').above(1)
        alert.save()
        alert_id = alert._id
        alert = self.conn.get_alert(name)
        assert alert._id == alert_id
        assert len(alert.conditions) == 1
        assert alert.conditions[0].condition_type == 'above'
        assert alert.conditions[0].metric_name == 'metric_test'

    def test_delete_alert(self):
        name = self.unique_name("test_delete_alert")
        alert = self.conn.create_alert(name)
        alert_id = alert._id
        alert = self.conn.get_alert(name)
        assert alert.name == name
        self.conn.delete_alert(name)
        time.sleep(2)
        # Make sure it's not there anymore
        try:
            alert = connection.get(names)
        except:
            alert = None
        assert(alert is None)

    def test_add_alert_with_a_service(self):
        name = self.unique_name("test_add_alert_with_a_service")
        alert = self.conn.create_alert(name)
        alert_id = alert._id
        alert.add_service(3747)
        alert.save()
        alert = self.conn.get_alert(name)
        assert len(alert.services) == 1
        assert len(alert.conditions) == 0
        assert alert.services[0]._id == 3747

    def test_add_alert_with_an_above_condition(self):
        name = self.unique_name("test_add_alert_with_an_above_condition")
        alert = self.conn.create_alert(name)
        alert_id = alert._id
        alert.add_condition_for('cpu').above(85).duration(70)
        alert.save()
        alert = self.conn.get_alert(name)
        assert len(alert.services) == 0
        assert alert.conditions[0].condition_type == 'above'
        assert alert.conditions[0]._duration == 70
        assert alert.conditions[0].threshold == 85
        assert alert.conditions[0].source == '*'

    def test_add_alert_with_an_absent_condition(self):
        name = self.unique_name("test_add_alert_with_an_absent_condition")
        alert = self.conn.create_alert(name)
        alert.add_condition_for('cpu').stops_reporting_for(60)
        alert.save()
        alert = self.conn.get_alert(name)
        assert len(alert.conditions) == 1
        condition = alert.conditions[0]
        assert condition.condition_type == 'absent'
        assert condition.metric_name == 'cpu'
        assert condition._duration == 60
        assert condition.source == '*'

    def test_add_alert_with_multiple_conditions(self):
        name = self.unique_name("test_add_alert_with_multiple_conditions")
        alert = self.conn.create_alert(name)
        alert.add_condition_for('cpu').above(0, 'sum')
        alert.add_condition_for('cpu').stops_reporting_for(3600)
        alert.add_condition_for('cpu').stops_reporting_for(3600)
        alert.add_condition_for('cpu').above(0, 'count')
        alert.save()

    def unique_name(self, prefix):
        name = prefix + str(time.time())
        self.alerts_created_during_test.append(name)
        return name


class TestSpacesApi(TestLibratoBase):
    @classmethod
    def setUpClass(cls):
        super(TestSpacesApi, cls).setUpClass()
        for space in cls.conn.list_spaces():
            cls.conn.delete_space(space.id)

    def test_create_space(self):
        space = self.conn.create_space("my space")
        self.assertIsNotNone(space.id)

    def test_get_space_by_id(self):
        space = self.conn.create_space("find me by id")
        self.wait_for_replication()
        found = self.conn.get_space(space.id)
        self.assertEqual(space.id, found.id)

    def test_find_space_by_name(self):
        # This assumes you only have 1 space with this name (it's not unique)
        space = self.conn.create_space("find me by name")
        self.wait_for_replication()
        found = self.conn.find_space(space.name)
        self.assertEqual(space.id, found.id)
        space.delete()

    def test_list_spaces(self):
        name = 'list me'
        space = self.conn.create_space(name)
        spaces = self.conn.list_spaces()
        self.assertTrue(name in [s.name for s in spaces])

    def test_delete_space(self):
        space = self.conn.create_space("delete me")
        self.wait_for_replication()
        self.conn.delete_space(space.id)

    def test_create_space_via_model(self):
        space = librato.Space(self.conn, 'Production')
        self.assertIsNone(space.id)
        space.save()
        self.assertIsNotNone(space.id)

    def test_delete_space_via_model(self):
        space = librato.Space(self.conn, 'delete me')
        space.save()
        self.wait_for_replication()
        space.delete()
        self.wait_for_replication()
        self.assertRaises(librato.exceptions.NotFound, self.conn.get_space, space.id)

    def test_create_chart(self):
        # Ensure metrics exist
        self.conn.submit('memory.free', 100)
        self.conn.submit('memory.used', 200)
        # Create space
        space = librato.Space(self.conn, 'my space')
        space.save()
        # Add chart
        chart = space.add_chart(
            'memory',
            type='line',
            streams=[
                {'metric': 'memory.free', 'source': '*'},
                {'metric': 'memory.used', 'source': '*',
                 'group_function': 'breakout', 'summary_function': 'average'}
            ],
            min=0,
            max=50,
            label='the y axis label',
            use_log_yaxis=True,
            related_space=1234
        )
        self.wait_for_replication()
        self.assertEqual(len(chart.streams), 2)

    def test_create_big_number(self):
        # Ensure metrics exist
        self.conn.submit('memory.free', 100)
        # Create space
        space = librato.Space(self.conn, 'my space')
        space.save()
        self.wait_for_replication()
        chart = space.add_chart(
            'memory',
            type='bignumber',
            streams=[
                {'metric': 'memory.free', 'source': '*'}
            ],
            use_last_value=False
        )

        # Shortcut
        chart2 = space.add_bignumber_chart('memory 2', 'memory.free', 'foo*',
                                           use_last_value=True)

        self.wait_for_replication()

        self.assertEqual(chart.type, 'bignumber')
        self.assertEqual(len(chart.streams), 1)
        self.assertFalse(chart.use_last_value)
        self.assertEqual(chart2.type, 'bignumber')
        self.assertEqual(len(chart2.streams), 1)
        self.assertTrue(chart2.use_last_value)


if __name__ == '__main__':
    # TO run a specific test:
    # $ nosetests tests/integration.py:TestLibratoBasic.test_update_metrics_attributes
    nose.runmodule()
