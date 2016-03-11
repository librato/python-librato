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
        return {'name': self.name,
                'charts': self.chart_ids}

    def charts(self):
        if self._charts is None:
            charts = []
            for c in self.chart_ids:
                charts.append(self.connection.get_chart_from_space_id(c, self.id))
            self._charts = charts

        return self._charts[:]

    def save(self):
        self.connection.update_space(self)


class Chart(object):
    def __init__(self, connection, name, id=None, type='line', streams=[]):
        self.connection = connection
        self.name = name
        self.type = 'line'
        self.streams = []
        for i in streams:
            if isinstance(i, Stream):
                self.streams.append(i)
            elif isinstance(i, dict):  # Probably parsing JSON here
                self.streams.append(Stream(i.get('metric'), i.get('source'), i.get('composite')))
            else:
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
                  streams=data.get('streams'))
        return obj

    def get_payload(self):
        return {'name': self.name,
                'type': self.type,
                'streams': self.streams_payload()}

    def streams_payload(self):
        return [s.get_payload() for s in self.streams]

    def new_stream(self, metric=None, source='*', composite=None):
        stream = Stream(metric, source, composite)
        self.streams.append(stream)
        return stream
