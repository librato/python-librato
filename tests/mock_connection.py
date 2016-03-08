from collections import OrderedDict
import json
import re

class MockServer(object):
    """Mock the data storing in the backend"""
    def __init__(self):
        self.clean()

    def clean(self):
        self.metrics = {'gauges': OrderedDict(), 'counters': OrderedDict()}
        self.instruments = OrderedDict()
        self.alerts = OrderedDict()
        self.dashboards = OrderedDict()
        self.spaces = OrderedDict()
        self.last_i_id = 0
        self.last_a_id = 0
        self.last_db_id = 0
        self.last_spc_id = 0
        self.last_chrt_id = 0

    def list_of_metrics(self):
        answer = self.__an_empty_list_metrics()
        for gn, g in self.metrics['gauges'].items():
            answer['metrics'].append(g)
        for cn, c in self.metrics['counters'].items():
            answer['metrics'].append(c)
        return json.dumps(answer).encode('utf-8')

    def create_metric(self, payload):
        for metric_type in ['gauge', 'counter']:
            for metric in payload.get(metric_type + 's', []):
                name = metric['name']
                self.add_metric_to_store(metric, metric_type)

                # The metric comes also with a value, we have to add it
                # to the measurements (for a particular source if available)
                if 'value' in metric:
                    if 'source' not in metric:
                        source = 'unassigned'
                    else:
                        source = metric['source']
                        del metric['source']
                    value = metric['value']
                    del metric['value']

                    # Create a new source for the measurements if necessary
                    p_to_metric = self.metrics[metric_type + 's'][name]
                    if source not in p_to_metric['measurements']:
                        p_to_metric['measurements'][source] = []
                    p_to_metric['measurements'][source].append({"value": value})

        return ''

    def list_of_instruments(self):
        answer = {}
        answer["query"] = {}
        answer["instruments"] = []
        ins = answer["instruments"]
        for _id, c_ins in self.instruments.items():
            c_ins["id"] = _id
            ins.append(c_ins)
        return json.dumps(answer).encode('utf-8')

    def create_instrument(self, payload):
        self.last_i_id += 1
        payload["id"] = self.last_i_id
        self.instruments[self.last_i_id] = payload
        return json.dumps(payload).encode('utf-8')

    def update_instrument(self, payload, uri):
        _id = None
        m = re.search('\/(\d+)$', uri)
        if m:
            _id = m.group(1)

        if int(_id) not in self.instruments:
            # TODO: return 400
            raise Exception("Trying to update instrument that doesn't " +
                            "exists %d", _id)
        else:
            self.instruments[int(_id)] = payload
            self.instruments[int(_id)]["id"] = int(_id)
        return ''

    def get_instrument(self, uri):
        _id = None
        m = re.search('\/(\d+)$', uri)
        if m:
            _id = m.group(1)

        if int(_id) not in self.instruments:
            # TODO: return 400
            raise Exception("Trying to get instrument that doesn't " +
                            " exists %d", _id)
        else:
            return json.dumps(self.instruments[int(_id)]).encode('utf-8')

    def __an_empty_list_metrics(self):
        answer = {}

    def create_alert(self, payload):
        self.last_a_id += 1
        payload["id"] = self.last_a_id
        payload["active"] = True
        self.alerts[self.last_a_id] = payload
        return json.dumps(payload).encode('utf-8')

    def get_alert(self, name, payload):
        return self.list_of_alerts(name)

    def delete_alert(self, _id, payload):
        del self.alerts[int(_id)]
        return ''

    def list_of_alerts(self, name=None):
        answer = {}
        answer["query"] = {}
        answer["alerts"] = []
        alert = answer["alerts"]
        for _id, c_alert in self.alerts.items():
            c_alert["id"] = _id
            if name is None:
                alert.append(c_alert)
            elif name==c_alert["name"]:
                alert.append(c_alert)
        return json.dumps(answer).encode('utf-8')

    def list_of_dashboards(self):
        answer = {}
        answer["query"] = {}
        answer["dashboards"] = []
        dbs = answer["dashboards"]
        for _id, c_dbs in self.dashboards.items():
            c_dbs["id"] = _id
            dbs.append(c_dbs)
        return json.dumps(answer).encode('utf-8')

    def list_of_spaces(self):
        answer = {}
        answer["query"] = {}
        answer["spaces"] = []
        spcs = answer["spaces"]
        for _id, c_spcs in self.spaces.items():
            c_spcs["id"] = _id
            spcs.append(c_spcs)
        return json.dumps(answer).encode('utf-8')

    def get_annotation_stream(self):
        name = 'My_Annotation'
        annotation_resp = {}
        annotation_resp['name'] = name
        annotation_resp['display_name'] = name
        annotation_resp['events'] = {'event':'mocked event'}
        annotation_resp['query'] = {'query': 'mocked query'}
        return json.dumps(annotation_resp).encode('utf-8')

    def create_space(self, payload):
        payload["id"] = self.last_spc_id
        payload.update({'charts': OrderedDict()})
        self.spaces[self.last_spc_id] = payload
        self.last_spc_id += 1
        return json.dumps(payload).encode('utf-8')

    def get_space(self, uri):
        _id = None
        m = re.search('\/(\d+)(\/charts)?$', uri)
        if m:
            _id = m.group(1)

        if int(_id) not in self.spaces:
            # TODO: return 400
            raise Exception("Trying to get space that doesn't " +
                            "exist %d", _id)
        else:
            return json.dumps(self.spaces[int(_id)]).encode('utf-8')

    def create_chart(self, uri, payload):
        _spc_id = None
        m = re.search('\/(\d+)\/charts$', uri)
        if m:
            _spc_id = m.group(1)

        if int(_spc_id) not in self.spaces:
            # TODO: return 400
            raise Exception("Trying to get space that doesn't " +
                            "exist %d", _spc_id)

        payload["id"] = self.last_chrt_id
        self.spaces[int(_spc_id)]['charts'][self.last_chrt_id] = payload
        self.last_chrt_id += 1
        return json.dumps(payload).encode('utf-8')

    def create_dashboard(self, payload):
        self.last_db_id += 1
        payload["id"] = self.last_i_id
        self.dashboards[self.last_i_id] = payload
        return json.dumps(payload).encode('utf-8')

    def list_of_charts_in_space(self, uri):
        _spc_id = None
        m = re.search('\/(\d+)\/charts$', uri)
        if m:
            _spc_id = m.group(1)

        if int(_spc_id) not in self.spaces:
            # TODO: return 400
            raise Exception("Trying to get space that doesn't " +
                            "exist %d", _spc_id)

        answer = {}
        answer["query"] = {}
        answer["charts"] = []
        chrts = answer["charts"]
        for _id, c_chrts in self.spaces[int(_spc_id)]['charts'].items():
            c_chrts["id"] = _id
            chrts.append(c_chrts)
        return json.dumps(answer).encode('utf-8')

    def update_chart_in_space(self, uri, payload):
        _spc_id = None
        _chrt_id = None
        m = re.search('\/spaces\/(\d+)\/charts\/(\d+)$', uri)
        if m:
            try:
                _spc_id = m.group(1)
                _chrt_id = m.group(2)
            except:
                raise Exception("Invalid URI %s" % uri)

        if int(_spc_id) not in self.spaces:
            # TODO: return 400
            raise Exception("Trying to update space that doesn't " +
                            "exists %d", _spc_id)
        elif int(_chrt_id) not in self.spaces[int(_spc_id)]['charts']:
            # TODO: return 400
            raise Exception("Trying to update chart that doesn't " +
                            "exists %d", _chrt_id)
        else:
            payload['id'] = int(_chrt_id)
            self.spaces[int(_chrt_id)]['charts'][int(_chrt_id)] = payload
        return ''

    def get_chart_from_space(self, uri):
        _spc_id = None
        _chrt_id = None
        m = re.search('\/spaces\/(\d+)\/charts\/(\d+)$', uri)
        if m:
            try:
                _spc_id = m.group(1)
                _chrt_id = m.group(2)
            except:
                raise Exception("Invalid URI %s" % uri)

        if int(_spc_id) not in self.spaces:
            # TODO: return 400
            raise Exception("Trying to get space that doesn't " +
                            "exists %d", _spc_id)
        elif int(_chrt_id) not in self.spaces[int(_spc_id)]['charts']:
            # TODO: return 400
            raise Exception("Trying to get chart that doesn't " +
                            "exists %d", _chrt_id)
        else:
            chart = self.spaces[int(_chrt_id)]['charts'][int(_chrt_id)]
            return json.dumps(chart).encode('utf-8')

    def update_space(self, uri, payload):
        _id = None
        m = re.search('\/(\d+)(\/charts)?$', uri)
        if m:
            _id = m.group(1)

        if int(_id) not in self.spaces:
            # TODO: return 400
            raise Exception("Trying to get space that doesn't " +
                            "exist %d", _id)
        else:
            self.spaces[int(_id)] = payload
            self.spaces[int(_id)]["id"] = int(_id)
        return ''

    def delete_space(self, uri):
        _id = None
        m = re.search('\/(\d+)(\/charts)?$', uri)
        if m:
            _id = m.group(1)

        if int(_id) not in self.spaces:
            # TODO: return 400
            raise Exception("Trying to get space that doesn't " +
                            "exist %d", _id)
        else:
            del self.spaces[int(_id)]
        return ''

    def delete_chart_from_space(self, uri):
        _spc_id = None
        _chrt_id = None
        m = re.search('\/spaces\/(\d+)\/charts\/(\d+)$', uri)
        if m:
            try:
                _spc_id = m.group(1)
                _chrt_id = m.group(2)
            except:
                raise Exception("Invalid URI %s" % uri)

        if int(_spc_id) not in self.spaces:
            # TODO: return 400
            raise Exception("Trying to update space that doesn't " +
                            "exists %d", _spc_id)
        elif int(_chrt_id) not in self.spaces[int(_spc_id)]['charts']:
            # TODO: return 400
            raise Exception("Trying to update chart that doesn't " +
                            "exists %d", _chrt_id)
        else:
            del self.spaces[int(_spc_id)]['charts'][int(_spc_id)]
        return ''

    def get_dashboard(self, uri):
        _id = None
        m = re.search('\/(\d+)$', uri)
        if m:
            _id = m.group(1)

        if int(_id) not in self.dashboards:
            # TODO: return 400
            raise Exception("Trying to get dashboard that doesn't " +
                            " exists %d", _id)
        else:
            return json.dumps(self.dashboards[int(_id)]).encode('utf-8')

    def update_dashboard(self, payload, uri):
        _id = None
        m = re.search('\/(\d+)$', uri)
        if m:
            _id = m.group(1)

        if int(_id) not in self.dashboards:
            # TODO: return 400
            raise Exception("Trying to update dashboard that doesn't " +
                            "exists %d", _id)
        else:
            self.dashboards[int(_id)] = payload
            self.dashboards[int(_id)]["id"] = int(_id)
        return ''

    def get_metric(self, name, payload):
        gauges = self.metrics['gauges']
        counters = self.metrics['counters']
        if name in gauges:
            metric = gauges[name]
        if name in counters:
            metric = counters[name]
        return json.dumps(metric).encode('utf-8')

    def delete_metric(self, name, payload):
        gauges = self.metrics['gauges']
        counters = self.metrics['counters']
        if not payload:
            payload = {}
        if 'names' not in payload:
            if name:
                payload['names'] = [name]
            else:
                raise Exception('Trying to DELETE metric without providing ' +
                                'a name or list of names')
        for rm_name in payload['names']:
            if rm_name in gauges:
                del gauges[rm_name]
            if rm_name in counters:
                del counters[rm_name]
        return ''

    def __an_empty_list_metrics(self):
        answer = {}
        answer['metrics'] = []
        answer['query'] = {}
        return answer

    def add_batch_of_measurements(self, gc_measurements):
        for gm in gc_measurements['gauges']:
            new_gauge = {'name': gm['name'], 'type': gm['type']}
            self.add_gauge_to_store(new_gauge)
            self.add_gauge_measurement(gm)

    def add_metric_to_store(self, g, m_type):
        if g['name'] not in self.metrics[m_type + 's']:
            g['type'] = m_type
            if 'period' not in g:
                g['period'] = None
            if 'attributes' not in g:
                g['attributes'] = {}
            g['measurements'] = {}
            self.metrics[m_type + 's'][g['name']] = g

    def delete_gauge(self, name):
        del self.gauges[name]
        return ''

'''Start the server.'''
server = MockServer()


class MockResponse(object):
    '''
    Inspect the request and interact with the mocked server to generate
    an answer.
    '''
    def __init__(self, request, fake_failure=False):
        self.request = request
        self.status = 500 if fake_failure else 200

    class headers(object):
        @staticmethod
        def get_content_charset(default):
            return 'utf-8'

    def read(self):
        return self._json_body_based_on_request()

    def _json_body_based_on_request(self):
        r = self.request
        if self._req_is_list_of_metrics():
            return server.list_of_metrics()
        elif self._req_is_create_metric():
            return server.create_metric(r.body)
        elif self._req_is_delete():
            #check for single delete. Batches don't include name in the url
            try:
                name = self._extract_from_url()
            except AttributeError:
                name = None
            return server.delete_metric(name, r.body)
        elif self._req_is_get_metric():
            return server.get_metric(self._extract_from_url(), r.body)

        elif self._req_is_list_of_instruments():
            return server.list_of_instruments()
        elif self._req_is_create_instrument():
            return server.create_instrument(r.body)
        elif self._req_is_update_instrument():
            return server.update_instrument(r.body, r.uri)
        elif self._req_is_get_instrument():
            return server.get_instrument(r.uri)

        elif self._req_is_list_of_alerts():
            return server.list_of_alerts()
        elif self._req_is_get_alert():
            return server.get_alert(self._extract_name_from_url_parameters(), r.body)
        elif self._req_is_create_alert():
            return server.create_alert(r.body)
        elif self._req_is_delete_alert():
            return server.delete_alert(self._extract_id_from_url(), r.body)
        elif self._req_is_list_of_dashboards():
            return server.list_of_dashboards()
        elif self._req_is_get_annotation_stream():
            return server.get_annotation_stream()
        elif self._req_is_create_dashboard():
            return server.create_dashboard(r.body)
        elif self._req_is_get_dashboard():
            return server.get_dashboard(r.uri)
        elif self._req_is_update_dashboard():
            return server.update_dashboard(r.body, r.uri)

        elif self._req_is_list_of_spaces():
            return server.list_of_spaces()
        elif self._req_is_get_space():
            return server.get_space(r.uri)
        elif self._req_is_list_of_charts_in_space():
            return server.list_of_charts_in_space(r.uri)
        elif self._req_is_get_chart_from_space():
            return server.get_chart_from_space(r.uri)
        elif self._req_is_create_space():
            return server.create_space(r.body)
        elif self._req_is_create_chart():
            return server.create_chart(r.uri, r.body)
        elif self._req_is_update_chart_in_space():
            return server.update_chart_in_space(r.uri, r.body)
        elif self._req_is_update_space():
            return server.update_space(r.uri, r.body)
        elif self._req_is_delete_space():
            return server.delete_space(r.uri)
        elif self._req_is_delete_chart_from_space():
            return server.delete_chart_from_space(r.uri)

        else:
            msg = """
      ----
      I am just mocking a RESTful Api server, I am not an actual server.
      path = %s
      method = %s
      ----
      """ % (self.request.uri, self.request.method)
            raise Exception(msg)

    def _req_is_list_of_metrics(self):
        return self._method_is('GET') and self._path_is('/v1/metrics')

    def _req_is_create_metric(self):
        return self._method_is('POST') and self._path_is('/v1/metrics')

    def _req_is_delete(self):
        return (self._method_is('DELETE') and not
                (re.match('/v1/alerts/\d+', self.request.uri) or
                (re.match('/v1/spaces/(\d+)(\/charts/\d+)?$', self.request.uri))))

    def _req_is_get_metric(self):
        return (self._method_is('GET') and
                re.match('/v1/metrics/([\w_]+)', self.request.uri))

    def _req_is_send_value(self, what):
        return (self._method_is('POST') and
                re.match('/v1/%s/([\w_]+).json' % what, self.request.uri))

    # Instruments
    def _req_is_create_instrument(self):
        return self._method_is('POST') and self._path_is('/v1/instruments')

    def _req_is_list_of_instruments(self):
        return self._method_is('GET') and self._path_is('/v1/instruments')

    def _req_is_update_instrument(self):
        return (self._method_is('PUT') and
                re.match('/v1/instruments/\d+', self.request.uri))

    def _req_is_get_instrument(self):
        return (self._method_is('GET') and
                re.match('/v1/instruments/\d+', self.request.uri))

    # Alerts
    def _req_is_create_alert(self):
        return self._method_is('POST') and self._path_is('/v1/alerts')
    def _req_is_list_of_alerts(self):
        return self._method_is('GET') and self._path_is('/v1/alerts?version=2') and not self._req_is_get_alert()
    def _req_is_get_alert(self):
        return self._method_is('GET') and re.match('/v1/alerts\?(version=2|name=.+)\&(name=.+|version=2)', self.request.uri)
    def _req_is_delete_alert(self):
        return (self._method_is('DELETE') and
                re.match('/v1/alerts/\d+', self.request.uri))

    # dashboards
    def _req_is_create_dashboard(self):
        return self._method_is('POST') and self._path_is('/v1/dashboards')

    def _req_is_list_of_dashboards(self):
        return self._method_is('GET') and self._path_is('/v1/dashboards')

    def _req_is_get_annotation_stream(self):
        return self._method_is('GET') and self._path_is('/v1/annotations/My_Annotation')

    def _req_is_get_dashboard(self):
        return (self._method_is('GET') and
                re.match('/v1/dashboards/\d+', self.request.uri))

    def _req_is_update_dashboard(self):
        return (self._method_is('PUT') and
                re.match('/v1/dashboards/\d+', self.request.uri))

    # TODO::
    # spaces
    def _req_is_list_of_spaces(self):
        return self._method_is('GET') and self._path_is('/v1/spaces')

    def _req_is_get_space(self):
        return (self._method_is('GET') and
                re.match('/v1/spaces/\d+$', self.request.uri))

    def _req_is_list_of_charts_in_space(self):
        return (self._method_is('GET') and
                re.match('/v1/spaces/\d+/charts$', self.request.uri))

    def _req_is_get_chart_from_space(self):
        return (self._method_is('GET') and
                re.match('/v1/spaces/\d+/charts/\d+', self.request.uri))

    def _req_is_create_space(self):
        return self._method_is('POST') and self._path_is('/v1/spaces')

    def _req_is_create_chart(self):
        return (self._method_is('POST') and
                re.match('/v1/spaces/\d+/charts$', self.request.uri))

    def _req_is_update_space(self):
        return (self._method_is('PUT') and
                re.match('/v1/spaces/\d+$', self.request.uri))

    def _req_is_update_chart_in_space(self):
        return (self._method_is('PUT') and
                re.match('/v1/spaces/\d+/charts/\d+', self.request.uri))

    def _req_is_delete_space(self):
        return (self._method_is('DELETE') and
                re.match('/v1/spaces/\d+$', self.request.uri))

    def _req_is_delete_chart_from_space(self):
        return (self._method_is('DELETE') and
                re.match('/v1/spaces/\d+/charts/\d+$', self.request.uri))

    def _method_is(self, m):
        return self.request.method == m

    def _path_is(self, p):
        return self.request.uri == p

    def _extract_from_url(self):
        m = re.match('/v1/metrics/([\w_]+)', self.request.uri)
        try:
            name = m.group(1)
        except:
            raise
        return name

    def _extract_id_from_url(self):
        m = re.match('/v1/alerts/([\w_]+)', self.request.uri)
        try:
            _id = m.group(1)
        except:
            raise
        return _id

    def _extract_name_from_url_parameters(self):
        m = re.match('.*name=([\w_]+)', self.request.uri)
        try:
            name = m.group(1)
        except:
            raise
        return name


class MockConnect(object):
    """
    Mocks urllib's HTTPSConnection.
    These are the methods we use in _mexec
    .request(method, uri, body, headers) : perform the request
    .getresponse()                       : return response object.
      .status
      .read() -> raw json body of the answer
    """
    def __init__(self, hostname, fake_n_errors=0, timeout=10):
        self.hostname = hostname
        self.fake_n_errors = fake_n_errors

    def request(self, method, uri, body, headers):
        self.method = method
        self.uri = uri
        self.headers = headers
        self.body = json.loads(body) if body else body

    def getresponse(self):
        if self.fake_n_errors > 0:
            fake_error = True
            self.fake_n_errors -= 1
        else:
            fake_error = False
        return MockResponse(self, fake_error)

    def close(self):
        pass
