# Copyright (c) 2013. Librato, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
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

import re
import six
import platform
import time
import logging
import os
from six.moves import http_client
from six.moves import map
from six import string_types
import urllib
import base64
import json
import email.message
from librato import exceptions
from librato.queue import Queue
from librato.metrics import Gauge, Counter, Metric
from librato.alerts import Alert, Service
from librato.annotations import Annotation
from librato.spaces import Space, Chart

__version__ = "3.1.0"

# Defaults
HOSTNAME = "metrics-api.librato.com"
BASE_PATH = "/v1/"
DEFAULT_TIMEOUT = 10

log = logging.getLogger("librato")

# Alias HTTPSConnection so the tests can mock it out.
HTTPSConnection = http_client.HTTPSConnection
HTTPConnection = http_client.HTTPConnection

# Alias urlencode, it moved between py2 and py3.
try:
    urlencode = urllib.parse.urlencode  # py3
except AttributeError:
    urlencode = urllib.urlencode        # py2


def sanitize_metric_name(metric_name):
    disallowed_character_pattern = r"(([^A-Za-z0-9.:\-_]|[\[\]]|\s)+)"
    max_metric_name_length = 255
    return re.sub(disallowed_character_pattern, '-', metric_name)[:max_metric_name_length]


def sanitize_no_op(metric_name):
    """
    Default behavior, some people want the error
    """
    return metric_name


class LibratoConnection(object):
    """Librato API Connection.
    Usage:
    >>> conn = LibratoConnection(username, api_key)
    >>> conn.list_metrics()
    [...]
    """

    def __init__(self, username, api_key, hostname=HOSTNAME, base_path=BASE_PATH, sanitizer=sanitize_no_op,
                 protocol="https", tags={}):
        """Create a new connection to Librato Metrics.
        Doesn't actually connect yet or validate until you make a request.

        :param username: The username (email address) of the user to connect as
        :type username: str
        :param api_key: The API Key (token) to use to authenticate
        :type api_key: str
        """
        try:
            self.username = username.encode('ascii')
            self.api_key = api_key.encode('ascii')
        except:
            raise TypeError("Librato only supports ascii for the credentials")

        if protocol not in ["http", "https"]:
            raise ValueError("Unsupported protocol: {}".format(protocol))

        self.custom_ua = None
        self.protocol = protocol
        self.hostname = hostname
        self.base_path = base_path
        # these two attributes ared used to control fake server errors when doing
        # unit testing.
        self.fake_n_errors = 0
        self.backoff_logic = lambda backoff: backoff * 2
        self.sanitize = sanitizer
        self.timeout = DEFAULT_TIMEOUT
        self.tags = dict(tags)

    def _compute_ua(self):
        if self.custom_ua:
            return self.custom_ua
        else:
            # http://en.wikipedia.org/wiki/User_agent#Format
            # librato-metrics/1.0.3 (ruby; 1.9.3p385; x86_64-darwin11.4.2) direct-faraday/0.8.4
            ua_chunks = []  # Set user agent
            ua_chunks.append("python-librato/" + __version__)
            p = platform
            system_info = (p.python_version(), p.machine(), p.system(), p.release())
            ua_chunks.append("(python; %s; %s-%s%s)" % system_info)
            return ' '.join(ua_chunks)

    def __getattr__(self, attr):
        def handle_undefined_method(*args):
            if re.search('dashboard|instrument', attr):
                print("We have deprecated support for instruments and dashboards.")
                print("https://github.com/librato/python-librato")
                print("")
            raise NotImplementedError()
        return handle_undefined_method

    def _set_headers(self, headers):
        """ set headers for request """
        if headers is None:
            headers = {}
        headers['Authorization'] = b"Basic " + base64.b64encode(self.username + b":" + self.api_key).strip()
        headers['User-Agent'] = self._compute_ua()
        return headers

    def _url_encode_params(self, params={}):
        if not isinstance(params, dict):
            raise Exception("You must pass in a dictionary!")
        params_list = []
        for k, v in params.items():
            if isinstance(v, list):
                params_list.extend([(k + '[]', x) for x in v])
            else:
                params_list.append((k, v))
        return urlencode(params_list)

    def _make_request(self, conn, path, headers, query_props, method):
        """ Perform the an https request to the server """
        uri = self.base_path + path
        body = None
        if query_props:
            if method == "POST" or method == "DELETE" or method == "PUT":
                body = json.dumps(query_props)
                headers['Content-Type'] = "application/json"
            else:
                uri += "?" + self._url_encode_params(query_props)

        log.info("method=%s uri=%s" % (method, uri))
        log.info("body(->): %s" % body)
        conn.request(method, uri, body=body, headers=headers)

        return conn.getresponse()

    def _process_response(self, resp, backoff):
        """ Process the response from the server """
        success = True
        resp_data = None
        not_a_server_error = resp.status < 500

        if not_a_server_error:
            resp_data = _decode_body(resp)
            a_client_error = resp.status >= 400
            if a_client_error:
                raise exceptions.get(resp.status, resp_data)
            return resp_data, success, backoff
        else:  # A server error, wait and retry
            backoff = self.backoff_logic(backoff)
            log.info("%s: waiting %s before re-trying" % (resp.status, backoff))
            time.sleep(backoff)
            return None, not success, backoff

    def _parse_tags_params(self, tags):
        result = {}
        for k, v in tags.items():
            result["tags[%s]" % k] = v
        return result

    def _mexe(self, path, method="GET", query_props=None, p_headers=None):
        """Internal method for executing a command.
           If we get server errors we exponentially wait before retrying
        """
        conn = self._setup_connection()
        headers = self._set_headers(p_headers)
        success = False
        backoff = 1
        resp_data = None
        while not success:
            resp = self._make_request(conn, path, headers, query_props, method)
            try:
                resp_data, success, backoff = self._process_response(resp, backoff)
            except http_client.ResponseNotReady:
                conn.close()
                conn = self._setup_connection()
        conn.close()
        return resp_data

    def _do_we_want_to_fake_server_errors(self):
        return self.fake_n_errors > 0

    def _setup_connection(self):
        connection_class = HTTPSConnection if self.protocol == "https" else HTTPConnection

        if self._do_we_want_to_fake_server_errors():
            return connection_class(self.hostname, fake_n_errors=self.fake_n_errors)
        else:
            return connection_class(self.hostname, timeout=self.timeout)

    def _parse(self, resp, name, cls):
        """Parse to an object"""
        if name in resp:
            return [cls.from_dict(self, m) for m in resp[name]]
        else:
            return resp

    # Get a shallow copy of the top-level tag set
    def get_tags(self):
        return dict(self.tags)

    # Define the top-level tag set for posting measurements
    def set_tags(self, d):
        self.tags = dict(d)    # Create a copy

    # Add to the top-level tag set
    def add_tags(self, d):
        self.tags.update(d)

    # Return all items for a "list" request
    def _get_paginated_results(self, entity, klass, **query_props):
        resp = self._mexe(entity, query_props=query_props)

        results = self._parse(resp, entity, klass)
        for result in results:
            yield result

        length = resp.get('query', {}).get('length', 0)
        offset = query_props.get('offset', 0) + length
        total = resp.get('query', {}).get('total', length)
        if offset < total and length > 0:
            query_props.update({'offset': offset})
            for result in self._get_paginated_results(entity, klass, **query_props):
                yield result

    #
    # Metrics
    #
    def list_metrics(self, **query_props):
        """List a page of metrics"""
        resp = self._mexe("metrics", query_props=query_props)
        return self._parse(resp, "metrics", Metric)

    def list_all_metrics(self, **query_props):
        return self._get_paginated_results("metrics", Metric, **query_props)

    def submit(self, name, value, type="gauge", **query_props):
        if 'tags' in query_props or self.get_tags():
            self.submit_tagged(name, value, **query_props)
        else:
            payload = {'gauges': [], 'counters': []}
            metric = {'name': self.sanitize(name), 'value': value}
            for k, v in query_props.items():
                metric[k] = v
            payload[type + 's'].append(metric)
            self._mexe("metrics", method="POST", query_props=payload)

    def submit_tagged(self, name, value, **query_props):
        payload = {'measurements': []}
        payload['measurements'].append(self.create_tagged_payload(name, value, **query_props))
        self._mexe("measurements", method="POST", query_props=payload)

    def create_tagged_payload(self, name, value, **query_props):
        """Create the measurement for forwarding to Librato"""
        measurement = {
            'name': self.sanitize(name),
            'value': value
        }
        if 'tags' in query_props:
            inherit_tags = query_props.pop('inherit_tags', False)
            if inherit_tags:
                tags = query_props.pop('tags', {})
                measurement['tags'] = dict(self.get_tags(), **tags)
        elif self.tags:
            measurement['tags'] = self.tags

        for k, v in query_props.items():
            measurement[k] = v
        return measurement

    def get(self, name, **query_props):
        resp = self._mexe("metrics/%s" % self.sanitize(name), method="GET", query_props=query_props)
        if resp['type'] == 'gauge':
            return Gauge.from_dict(self, resp)
        elif resp['type'] == 'counter':
            return Counter.from_dict(self, resp)
        else:
            raise Exception('The server sent me something that is not a Gauge nor a Counter.')

    def get_tagged(self, name, **query_props):
        """Fetches multi-dimensional metrics"""
        if 'resolution' not in query_props:
            # Default to raw resolution
            query_props['resolution'] = 1
        if 'start_time' not in query_props and 'duration' not in query_props:
            raise Exception("You must provide 'start_time' or 'duration'")
        if 'start_time' in query_props and 'end_time' in query_props and 'duration' in query_props:
            raise Exception("It is an error to set 'start_time', 'end_time' and 'duration'")

        if 'tags' in query_props:
            parsed_tags = self._parse_tags_params(query_props.pop('tags'))
            query_props.update(parsed_tags)

        return self._mexe("measurements/%s" % self.sanitize(name), method="GET", query_props=query_props)

    def get_measurements(self, name, **query_props):
        return self.get_tagged(name, **query_props)

    def get_composite(self, compose, **query_props):
        if self.get_tags():
            return self.get_composite_tagged(compose, **query_props)
        else:
            if 'resolution' not in query_props:
                # Default to raw resolution
                query_props['resolution'] = 1
            if 'start_time' not in query_props:
                raise Exception("You must provide a 'start_time'")
            query_props['compose'] = compose
            return self._mexe('metrics', method="GET", query_props=query_props)

    def get_composite_tagged(self, compose, **query_props):
        if 'resolution' not in query_props:
            # Default to raw resolution
            query_props['resolution'] = 1
        if 'start_time' not in query_props:
            raise Exception("You must provide a 'start_time'")
        query_props['compose'] = compose
        return self._mexe('measurements', method="GET", query_props=query_props)

    def create_composite(self, name, compose, **query_props):
        query_props['composite'] = compose
        query_props['type'] = 'composite'
        return self.update(name, **query_props)

    def update(self, name, **query_props):
        return self._mexe("metrics/%s" % self.sanitize(name), method="PUT", query_props=query_props)

    def delete(self, names):
        if isinstance(names, six.string_types):
            names = self.sanitize(names)
        else:
            names = list(map(self.sanitize, names))
        path = "metrics/%s" % names
        payload = {}
        if not isinstance(names, string_types):
            payload = {'names': names}
            path = "metrics"
        return self._mexe(path, method="DELETE", query_props=payload)

    #
    # Annotations
    #
    def list_annotation_streams(self, **query_props):
        """List all annotation streams"""
        return self._get_paginated_results('annotations', Annotation, **query_props)

    def get_annotation_stream(self, name, **query_props):
        """Get an annotation stream (add start_date to query props for events)"""
        resp = self._mexe("annotations/%s" % name, method="GET", query_props=query_props)
        return Annotation.from_dict(self, resp)

    def get_annotation(self, name, id, **query_props):
        """Get a specific annotation event by ID"""
        resp = self._mexe("annotations/%s/%s" % (name, id), method="GET", query_props=query_props)
        return Annotation.from_dict(self, resp)

    def update_annotation_stream(self, name, **query_props):
        """Update an annotation streams metadata"""
        payload = Annotation(self, name).get_payload()
        for k, v in query_props.items():
            payload[k] = v
        resp = self._mexe("annotations/%s" % name, method="PUT", query_props=payload)
        return Annotation.from_dict(self, resp)

    def post_annotation(self, name, **query_props):
        """ Create an annotation event on :name. """
        """ If the annotation stream does not exist, it will be created automatically. """
        resp = self._mexe("annotations/%s" % name, method="POST", query_props=query_props)
        return resp

    def delete_annotation_stream(self, name, **query_props):
        """delete an annotation stream """
        resp = self._mexe("annotations/%s" % name, method="DELETE", query_props=query_props)
        return resp

    #
    # Alerts
    #
    def create_alert(self, name, **query_props):
        """Create a new alert"""
        payload = Alert(self, name, **query_props).get_payload()
        resp = self._mexe("alerts", method="POST", query_props=payload)
        return Alert.from_dict(self, resp)

    def update_alert(self, alert, **query_props):
        """Update an existing alert"""
        payload = alert.get_payload()
        for k, v in query_props.items():
            payload[k] = v
        resp = self._mexe("alerts/%s" % alert._id,
                          method="PUT", query_props=payload)
        return resp

    # Delete an alert by name (not by id)
    def delete_alert(self, name):
        """delete an alert"""
        alert = self.get_alert(name)
        if alert is None:
            return None
        resp = self._mexe("alerts/%s" % alert._id, method="DELETE")
        return resp

    def get_alert(self, name):
        """Get specific alert"""
        resp = self._mexe("alerts", query_props={'name': name})
        alerts = self._parse(resp, "alerts", Alert)
        if len(alerts) > 0:
            return alerts[0]
        return None

    def list_alerts(self, active_only=True, **query_props):
        """List all alerts (default to active only)"""
        return self._get_paginated_results("alerts", Alert, **query_props)

    def list_services(self, **query_props):
        # Note: This API currently does not have the ability to
        # filter by title, type, etc
        return self._get_paginated_results("services", Service, **query_props)

    #
    # Spaces
    #
    def list_spaces(self, **query_props):
        """List all spaces"""
        return self._get_paginated_results("spaces", Space, **query_props)

    def get_space(self, id, **query_props):
        """Get specific space by ID"""
        resp = self._mexe("spaces/%s" % id,
                          method="GET", query_props=query_props)
        return Space.from_dict(self, resp)

    def find_space(self, name):
        if type(name) is int:
            raise ValueError("This method expects name as a parameter, %s given" % name)
        """Find specific space by Name"""
        spaces = self.list_spaces(name=name)
        # Find the Space by name (case-insensitive)
        # This returns the first space found matching the name
        for space in spaces:
            if space.name and space.name.lower() == name.lower():
                # Now use the ID to hydrate the space attributes (charts)
                return self.get_space(space.id)

        return None

    def update_space(self, space, **query_props):
        """Update an existing space (API currently only allows update of name"""
        payload = space.get_payload()
        for k, v in query_props.items():
            payload[k] = v
        resp = self._mexe("spaces/%s" % space.id,
                          method="PUT", query_props=payload)
        return resp

    def create_space(self, name, **query_props):
        payload = Space(self, name).get_payload()
        for k, v in query_props.items():
            payload[k] = v
        resp = self._mexe("spaces", method="POST", query_props=payload)
        return Space.from_dict(self, resp)

    def delete_space(self, id):
        """delete a space"""
        resp = self._mexe("spaces/%s" % id, method="DELETE")
        return resp

    #
    # Charts
    #
    def list_charts_in_space(self, space, **query_props):
        """List all charts from space"""
        resp = self._mexe("spaces/%s/charts" % space.id, query_props=query_props)
        # "charts" is not in the response, but make this
        # actually return Chart objects
        charts = self._parse({"charts": resp}, "charts", Chart)
        # Populate space ID
        for chart in charts:
            chart.space_id = space.id
        return charts

    def get_chart(self, chart_id, space_or_space_id, **query_props):
        """Get specific chart by ID from Space"""
        space_id = None
        if type(space_or_space_id) is int:
            space_id = space_or_space_id
        elif type(space_or_space_id) is Space:
            space_id = space_or_space_id.id
        else:
            raise ValueError("Space parameter is invalid")
        # TODO: Add better handling around 404s
        resp = self._mexe("spaces/%s/charts/%s" % (space_id, chart_id), method="GET", query_props=query_props)
        resp['space_id'] = space_id
        return Chart.from_dict(self, resp)

    # Find a chart by name in a space. Return the first match, so if multiple
    # charts have the same name, you'll only get the first one
    def find_chart(self, name, space):
        charts = self.list_charts_in_space(space)
        for chart in charts:
            if chart.name and chart.name.lower() == name.lower():
                # Now use the ID to hydrate the chart attributes (streams)
                return self.get_chart(chart.id, space)
        return None

    def create_chart(self, name, space, **query_props):
        """Create a new chart in space"""
        payload = Chart(self, name).get_payload()
        for k, v in query_props.items():
            payload[k] = v
        resp = self._mexe("spaces/%s/charts" % space.id, method="POST", query_props=payload)
        resp['space_id'] = space.id
        return Chart.from_dict(self, resp)

    def update_chart(self, chart, space, **query_props):
        """Update an existing chart"""
        payload = chart.get_payload()
        for k, v in query_props.items():
            payload[k] = v
        resp = self._mexe("spaces/%s/charts/%s" % (space.id, chart.id),
                          method="PUT",
                          query_props=payload)
        return resp

    def delete_chart(self, chart_id, space_id, **query_props):
        """delete a chart from a space"""
        resp = self._mexe("spaces/%s/charts/%s" % (space_id, chart_id), method="DELETE")
        return resp

    #
    # Queue
    #
    def new_queue(self, **kwargs):
        return Queue(self, **kwargs)

    #
    # misc
    #
    def set_timeout(self, timeout):
        self.timeout = timeout


def connect(username=None, api_key=None, hostname=HOSTNAME, base_path=BASE_PATH, sanitizer=sanitize_no_op,
            protocol="https", tags={}):
    """
    Connect to Librato Metrics
    """

    username = username if username else os.getenv('LIBRATO_USER', '')
    api_key = api_key if api_key else os.getenv('LIBRATO_TOKEN', '')

    return LibratoConnection(username, api_key, hostname, base_path, sanitizer=sanitizer, protocol=protocol, tags=tags)


def _decode_body(resp):
    """
    Read and decode HTTPResponse body based on charset and content-type
    """
    body = resp.read()
    log.info("body(<-): %s" % body)
    if not body:
        return None

    decoded_body = body.decode(_getcharset(resp))
    content_type = _get_content_type(resp)

    if content_type == "application/json":
        resp_data = json.loads(decoded_body)
    else:
        resp_data = decoded_body

    return resp_data


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


def _get_content_type(resp):
    """
    Get Content-Type header ignoring parameters
    """
    parts = resp.getheader('content-type', "application/json").split(";")
    return parts[0]
