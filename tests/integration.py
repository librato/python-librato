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
import nose
logging.basicConfig(level=logging.DEBUG)

class TestLibratoBasic(object):
  @classmethod
  def setup_class(cls):
    """Initialize the Librato Connection"""
    import librato
    import os
    assert(os.environ.has_key("LIBRATO_USER") and os.environ.has_key("LIBRATO_TOKEN")), \
           "Must set LIBRATO_USER and LIBRATO_TOKEN to run tests"
    cls.conn = librato.connect(os.environ['LIBRATO_USER'], os.environ['LIBRATO_TOKEN'])

  def test_list_metrics(self):
    metrics = self.conn.list_metrics()

  def test_create_and_delete_gauge(self):
    gauge = self.conn.create_gauge("Test", "Test Gauge to be removed")
    assert(gauge and gauge.name == "Test")
    assert(gauge.description == "Test Gauge to be removed")
    # Clean up gague
    self.conn.delete_gauge("Test")
    # Make sure it's not there anymore
    gauge = None
    try:
      gauge = self.conn.get_gauge("Test")
    except:
      gauge = None
    assert(gauge is None)

  def test_create_and_delete_counter(self):
    counter = self.conn.create_counter("TestC", "Test Counter to be removed")
    assert(counter and counter.name == "TestC")
    assert(counter.description == "Test Counter to be removed")
    # Clean up gague
    self.conn.delete_counter("TestC")
    # Make sure it's not there anymore
    counter = None
    try:
      counter = self.conn.get_counter("TestC")
    except:
      counter = None
    assert(counter is None)

  def test_save_gauge_metrics(self):
    try:
      gauge = self.conn.create_gauge("Test_sg", "Test Gauge")
    except:
      gauge = self.conn.get_gauge("Test_sg")
    self.conn.send_gauge_value("Test_sg", 11111)
    self.conn.send_gauge_value("Test_sg", 22222)
    self.conn.delete_gauge("Test_sg")

  def test_send_batch_gauge_measurements(self):
    try:
      gauge = self.conn.create_gauge("home_temp", "temperature at home")
    except:
      gauge = self.conn.get_gauge("home_temp")
    gauge.push(15, "upstairs")
    gauge.push(25, "dowstairs")
    assert gauge.measurements.has_key('gauges')
    assert len(gauge.measurements['gauges']) == 2
    gauge.submit()
    # We should have measurements now
    assert len(gauge.measurements['gauges']) == 0
    #self.conn.delete_gauge("home_temp")

  def test_send_batch_counter_measurements(self):
    try:
      counter = self.conn.create_counter("conn_servers", "# of connections to server")
    except:
      counter = self.conn.get_counter("conn_servers")
    counter.push(150, "server1")
    counter.push(200, "server2")
    assert counter.measurements.has_key('counters')
    assert len(counter.measurements['counters']) == 2
    counter.submit()
    # We should have measurements now
    assert len(counter.measurements['counters']) == 0
    #self.conn.delete_gauge("home_temp")

if __name__ == '__main__':
    nose.runmodule()
