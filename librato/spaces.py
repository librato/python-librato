from librato.streams import Stream


class Space(object):
    """Librato Space Base class"""

    def __init__(self, connection, name, id=None, chart_dicts=None):
        self.connection = connection
        self.name = name
        self.chart_ids = []
        self._charts = None
        for c in (chart_dicts or []):
            self.chart_ids.append(c['id'])
        self.id = id

    @classmethod
    def from_dict(cls, connection, data):
        """
        Returns a Space object from a dictionary item,
        which is usually from librato's API
        """
        obj = cls(connection,
                  data['name'],
                  id=data['id'],
                  chart_dicts=data.get('charts'))
        return obj

    def get_payload(self):
        return {'name': self.name}

    def charts(self):
        if self._charts is None or self._charts == []:
            self._charts = self.connection.list_charts_in_space(self)
        return self._charts[:]

    def new_chart(self, name, type='line', streams=[], use_last_value=None):
        return Chart(self.connection, name, type=type,
                     space_id=self.id, streams=streams,
                     use_last_value=use_last_value)

    def add_chart(self, name, type='line', streams=[], use_last_value=None):
        chart = self.new_chart(name, type=type, streams=streams,
                               use_last_value=use_last_value)
        chart.save()
        return chart

    def add_line_chart(self, name, streams=[]):
        return self.add_chart(name, streams=streams)

    def add_single_line_chart(self, name, metric=None, source='*',
                              group_function=None, summary_function=None):
        stream = {'metric': metric, 'source': source}

        if group_function:
            stream['group_function'] = group_function
        if summary_function:
            stream['summary_function'] = summary_function
        return self.add_line_chart(name, streams=[stream])

    def add_stacked_chart(self, name, streams=[]):
        return self.add_chart(name, type='stacked', streams=streams)

    def add_single_stacked_chart(self, name, metric, source='*'):
        stream = {'metric': metric, 'source': source}
        return self.add_stacked_chart(name, streams=[stream])

    def add_bignumber_chart(self, name, metric, source='*',
                            summary_function='average', use_last_value=True):
        stream = {
            'metric': metric,
            'source': source,
            'summary_function': summary_function
        }
        chart = self.add_chart(name, type='bignumber',
                               use_last_value=use_last_value, streams=[stream])
        return chart

    # This currently only updates the name of the Space
    def save(self):
        self.connection.update_space(self)

    def rename(self, new_name):
        self.name = new_name
        self.save()

    def delete(self):
        return self.connection.delete_space(self.id)


class Chart(object):
    # Payload example from /spaces/123/charts/456 API
    # {
    #   "id": 1723352,
    #   "name": "Hottest City",
    #   "type": "line",
    #   "streams": [
    #     {
    #       "id": 19261984,
    #       "metric": "apparent_temperature",
    #       "type": "gauge",
    #       "source": "*",
    #       "group_function": "max",
    #       "summary_function": "max"
    #     }
    #   ],
    #   "max": 105,
    #   "min": 0,
    #   "related_space": 96893,
    #   "label": "The y axis label",
    #   "use_log_yaxis": true
    # }
    def __init__(self, connection, name=None, id=None, type='line',
                 space_id=None, streams=[],
                 min=None, max=None,
                 label=None,
                 use_log_yaxis=None,
                 use_last_value=None):
        self.connection = connection
        self.name = name
        self.type = type
        self.space_id = space_id
        self._space = None
        self.streams = []
        self.label = label
        self.use_log_yaxis = use_log_yaxis
        self.min = min
        self.max = max
        self.use_last_value = use_last_value
        for i in streams:
            if isinstance(i, Stream):
                self.streams.append(i)
            elif isinstance(i, dict):  # Probably parsing JSON here
                # dict
                self.streams.append(Stream(**i))
            else:
                # list?
                self.streams.append(Stream(*i))
        self.id = id

    @classmethod
    def from_dict(cls, connection, data):
        """
        Returns a Chart object from a dictionary item,
        which is usually from librato's API
        """
        obj = cls(connection,
                  data['name'],
                  id=data['id'],
                  type=data.get('type', 'line'),
                  space_id=data.get('space_id'),
                  streams=data.get('streams'))
        return obj

    def space(self):
        if self._space is None and self.space_id is not None:
            # Find the Space
            self._space = self.connection.get_space(self.space_id)
        return self._space

    def get_payload(self):
        payload = {
            'name': self.name,
            'type': self.type,
            'streams': self.streams_payload()
        }
        if self.use_last_value is not None:
            payload['use_last_value'] = self.use_last_value
        return payload

    def streams_payload(self):
        return [s.get_payload() for s in self.streams]

    def new_stream(self, metric=None, source='*', composite=None):
        stream = Stream(metric, source, composite)
        self.streams.append(stream)
        return stream

    def persisted(self):
        return self.id is not None

    def save(self):
        if self.persisted():
            return self.connection.update_chart(self, self.space())
        else:
            args = {
                'type': self.type,
                'streams': self.streams_payload(),
            }
            if self.use_last_value:
                args['use_last_value'] = self.use_last_value
            resp = self.connection.create_chart(self.name, self.space(),
                                                **args)
            self.id = resp.id
            return resp

    def rename(self, new_name):
        self.name = new_name
        self.save()

    def delete(self):
        return self.connection.delete_chart(self.id, self.space_id)
