# Copyright (c) 2013. Librato, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Librato, Inc. nor the names of project contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL LIBRATO, INC. BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
__version__ = "0.3"

# Defaults
HOSTNAME = "metrics-api.librato.com"
BASE_PATH = "/v1/"

import time
import logging
from httplib import HTTPSConnection
import urllib
import base64
import json
from librato import exceptions
from librato.queue import Queue

log = logging.getLogger("librato")

class LibratoConnection(object):
  """Librato API Connection.
  Usage:
  >>> conn = LibratoConnection(username, api_key)
  >>> conn.list_metrics()
  [...]
  """

  def __init__(self, username, api_key, hostname=HOSTNAME, base_path=BASE_PATH):
    """Create a new connection to Librato Metrics.
    Doesn't actually connect yet or validate until you
    make a request.

    :param username: The username (email address) of the user to connect as
    :type username: str
    :param api_key: The API Key (token) to use to authenticate
    :type api_key: str
    """
    self.username = username
    self.api_key = api_key
    self.hostname = hostname
    self.base_path = base_path

  def _mexe(self, path, method="GET", query_props=None, headers=None):
    """Internal method for exeucting a command"""

    success = False
    backoff = 1

    if headers is None:
      headers = {}
    headers['Authorization'] = "Basic " + base64.b64encode(self.username + ":" + self.api_key).strip()
    resp_data = None

    while not success:
      conn = HTTPSConnection(self.hostname)
      uri  = self.base_path + path
      body = None
      if query_props:
        if method == "POST":
          body = json.dumps(query_props)
          headers['Content-Type'] = "application/json"
        else:
          uri += "?" + urllib.urlencode(query_props)

      log.info("method=%s uri=%s" % (method, uri))
      log.info("body(->): %s" % body)
      conn.request(method, uri, body=body, headers=headers)
      resp = conn.getresponse()
      if resp.status < 500:
        body = resp.read()
        if body:
          try:
            resp_data = json.loads(body)
          except:
            pass
        log.info("body(<-): %s" % body)
        if resp.status >= 400:
          raise exceptions.get(resp.status, resp_data)
        success = True
      else:
        backoff += backoff*2
        log.info("%s: waiting %s before re-trying" % (resp.status, backoff))
        time.sleep(backoff)
    log.info("-" * 80)
    return resp_data

  def _parse(self, resp, name, cls):
    """Parse to an object"""
    if resp.has_key(name):
      return [cls.from_dict(self, m) for m in resp[name]]
    else:
      return resp

  #
  # Metrics
  #
  def list_metrics(self, **query_props):
    """List all the metrics available"""
    from librato.metrics import Metric
    resp = self._mexe("metrics.json", query_props=query_props)
    return self._parse(resp, "metrics", Metric)

  def post_metrics(self, metric_data):
    """Posts multiple metrics using the
      http://dev.librato.com/v1/post/metrics
    API"""
    return self._mexe("metrics.json", method="POST", query_props=metric_data)

  #
  # Gauges
  #
  def list_gauges(self, **query_props):
    """List all available gauges"""
    from librato.metrics import Gauge
    resp = self._mexe("gauges.json", query_props=query_props)
    return self._parse(resp, "gauges", Gauge)

  def create_gauge(self, name, description=None, **query_props):
    """Create a new gauge"""
    from librato.metrics import Gauge
    if query_props is None:
      query_props = {}
    query_props['name'] = name
    if description:
      query_props['description'] = description
    resp = self._mexe("gauges.json", method="POST", query_props=query_props)
    return Gauge.from_dict(self, resp)

  def get_gauge(self, name, **query_props):
    """Fetch a specific gauge"""
    from librato.metrics import Gauge
    resp = self._mexe("gauges/%s.json" % name, method="GET", query_props=query_props)
    return Gauge.from_dict(self, resp)

  def delete_gauge(self, name):
    """Delete a guage"""
    return self._mexe("gauges/%s.json" % name, method="DELETE")

  def send_gauge_value(self, name, value, source=None, **params):
    """Send a value for a given gauge"""
    if not params:
      params = {}
    params["value"] = value
    if source:
      params["source"] = source
    return self._mexe("gauges/%s.json" % name, method="POST", query_props=params)

  #
  # Counters
  #
  def list_counters(self, **query_props):
    """List all available counters"""
    from librato.metrics import Counter
    resp = self._mexe("counters.json", query_props=query_props)
    return self._parse(resp, "counters", Counter)

  def create_counter(self, name, description=None, **query_props):
    """Create a new counter"""
    from librato.metrics import Counter
    if query_props is None:
      query_props = {}
    query_props['name'] = name
    if description:
      query_props['description'] = description
    resp = self._mexe("counters.json", method="POST", query_props=query_props)
    return Counter.from_dict(self, resp)

  def get_counter(self, name, **query_props):
    """Fetch a specific counter"""
    from librato.metrics import Counter
    resp = self._mexe("counters/%s.json" % name, method="GET", query_props=query_props)
    return Counter.from_dict(self, resp)

  def delete_counter(self, name):
    """Delete a counter"""
    return self._mexe("counters/%s.json" % name, method="DELETE")

  def send_counter_value(self, name, value, source=None, **params):
    """Send a value for a given counter"""
    if not params:
      params = {}
    params["value"] = value
    if source:
      params["source"] = source
    return self._mexe("counters/%s.json" % name, method="POST", query_props=params)

  #
  # Queue
  #
  def new_queue(self):
    return Queue(self)

def connect(username, api_key, hostname=HOSTNAME, base_path=BASE_PATH):
  """Connect to Librato Metrics"""
  return LibratoConnection(username, api_key, hostname, base_path)

