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
__version__ = "0.2.5"

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
from librato.metrics import Gauge, Counter

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
        if method == "POST" or method == "DELETE":
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
    resp = self._mexe("metrics", query_props=query_props)
    return self._parse(resp, "metrics", Metric)

  def submit(self, name, value, type="gauge", **query_props):
    payload = {'gauges': [], 'counters': []}
    metric = { 'name': name, 'value': value }
    for k,v in query_props.items():
      metric[k] = v
    payload[type + 's'].append(metric)
    self._mexe("metrics", method="POST", query_props=payload)

  def get(self, name, **query_props):
    resp = self._mexe("metrics/%s" % name, method="GET", query_props=query_props)
    if resp['type'] == 'gauge':
      return Gauge.from_dict(self, resp)
    elif resp['type'] == 'counter':
      return Gauge.from_dict(self, resp)
    else:
      raise Exception('The server sent me something that is not a Gauge nor a Counter.')

  def delete(self, name):
    payload = { 'names': [name] }
    return self._mexe("metrics", method="DELETE", query_props=payload)

  #
  # Queue
  #
  def new_queue(self):
    return Queue(self)

def connect(username, api_key, hostname=HOSTNAME, base_path=BASE_PATH):
  """Connect to Librato Metrics"""
  return LibratoConnection(username, api_key, hostname, base_path)

