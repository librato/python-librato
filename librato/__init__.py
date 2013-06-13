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
__version__ = "0.4.5"

# Defaults
HOSTNAME = "metrics-api.librato.com"
BASE_PATH = "/v1/"

import platform
import time
import logging
from six.moves import http_client
import urllib
import base64
import json
import email.message
from librato import exceptions
from librato.queue import Queue
from librato.metrics import Gauge, Counter

log = logging.getLogger("librato")

# Alias HTTPSConnection so the tests can mock it out.
HTTPSConnection = http_client.HTTPSConnection

# Alias urlencode, it moved between py2 and py3.
try:
    urlencode = urllib.parse.urlencode  # py3
except AttributeError:
    urlencode = urllib.urlencode        # py2

class LibratoConnection(object):
  """Librato API Connection.
  Usage:
  >>> conn = LibratoConnection(username, api_key)
  >>> conn.list_metrics()
  [...]
  """

  def __init__(self, username, api_key, hostname=HOSTNAME, base_path=BASE_PATH):
    """Create a new connection to Librato Metrics.
    Doesn't actually connect yet or validate until you make a request.

    :param username: The username (email address) of the user to connect as
    :type username: str
    :param api_key: The API Key (token) to use to authenticate
    :type api_key: str
    """
    self.username      = username.encode('ascii')   # FIXME: can usernames be non-ASCII?
    self.api_key       = api_key.encode('ascii')    # FIXME: ditto.
    self.hostname      = hostname
    self.base_path     = base_path
    # these two attributes ared used to control fake server errors when doing
    # unit testing.
    self.fake_n_errors = 0
    self.backoff_logic = lambda backoff: backoff*2

  def _set_headers(self, headers):
    """ set headers for request """
    if headers is None:
      headers = {}
    headers['Authorization'] = b"Basic " + base64.b64encode(self.username + b":" + self.api_key).strip()

    # http://en.wikipedia.org/wiki/User_agent#Format
    # librato-metrics/1.0.3 (ruby; 1.9.3p385; x86_64-darwin11.4.2) direct-faraday/0.8.4
    ua_chunks = [] # Set user agent
    ua_chunks.append("python-librato/" + __version__)
    p = platform
    system_info = (p.python_version(), p.machine(), p.system(), p.release())
    ua_chunks.append("(python; %s; %s-%s%s)" %  system_info)
    headers['User-Agent'] = ' '.join(ua_chunks)
    return headers

  def _make_request(self, conn, path, headers, query_props, method):
    """ Perform the an https request to the server """
    uri  = self.base_path + path
    body = None
    if query_props:
      if method == "POST" or method == "DELETE" or method == "PUT":
        body = json.dumps(query_props)
        headers['Content-Type'] = "application/json"
      else:
        uri += "?" + urlencode(query_props)

    log.info("method=%s uri=%s" % (method, uri))
    log.info("body(->): %s" % body)
    conn.request(method, uri, body=body, headers=headers)
    return conn.getresponse()

  def _process_response(self, resp, backoff):
    """ Process the response from the server """
    success            = True
    resp_data          = None
    not_a_server_error = resp.status < 500

    if not_a_server_error:
      body = resp.read()
      if body:
        resp_data = json.loads(body.decode(_getcharset(resp)))
      log.info("body(<-): %s" % body)
      a_client_error = resp.status >= 400
      if a_client_error:
        raise exceptions.get(resp.status, resp_data)
      return resp_data, success, backoff
    else: # A server error, wait and retry
      backoff = self.backoff_logic(backoff)
      log.info("%s: waiting %s before re-trying" % (resp.status, backoff))
      time.sleep(backoff)
      return None, not success, backoff

  def _mexe(self, path, method="GET", query_props=None, p_headers=None):
    """Internal method for executing a command.
       If we get server errors we exponentially wait before retrying
    """
    conn      = self._setup_connection()
    headers   = self._set_headers(p_headers)
    success   = False
    backoff   = 1
    resp_data = None
    while not success:
      resp = self._make_request(conn, path, headers, query_props, method)
      resp_data, success, backoff = self._process_response(resp, backoff)
    return resp_data

  def _do_we_want_to_fake_server_errors(self):
    return self.fake_n_errors > 0

  def _setup_connection(self):
    if self._do_we_want_to_fake_server_errors():
      return HTTPSConnection(self.hostname, fake_n_errors=self.fake_n_errors)
    else:
      return HTTPSConnection(self.hostname)

  def _parse(self, resp, name, cls):
    """Parse to an object"""
    if name in resp:
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

  def update(self, name, **query_props):
    resp = self._mexe("metrics/%s" % name, method="PUT", query_props=query_props)

  def delete(self, name):
    payload = { 'names': [name] }
    return self._mexe("metrics", method="DELETE", query_props=payload)

  #
  # Queue
  #
  def new_queue(self):
    return Queue(self)

def connect(username, api_key, hostname=HOSTNAME, base_path=BASE_PATH):
  """
  Connect to Librato Metrics
  """
  return LibratoConnection(username, api_key, hostname, base_path)

def _getcharset(resp, default='utf-8'):
    """
    Extract the charset from an HTTPResponse.
    """
    # In Python 3, HTTPResponse is a subclass of email.message.Message, so we
    # can use get_content_chrset. In Python 2, however, it's not so we have
    # to be "clever".
    if hasattr(resp, 'headers'):
        return resp.headers.get_content_charset(default)
    else:
        m = email.message.Message()
        m['content-type'] = resp.getheader('content-type')
        return m.get_content_charset(default)
