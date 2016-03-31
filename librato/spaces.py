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

    def new_chart(self, name, type='line'):
        return Chart(self.connection, name, id=None, type=type, space_id=self.id)

    # This currently only updates the name of the Space
    def save(self):
        self.connection.update_space(self)

    def rename(self, new_name):
        self.name = new_name
        self.save()

    def delete(self):
        return self.connection.delete_space(self.id)


class Chart(object):
    def __init__(self, connection, name, id=None, type='line', space_id=None, streams=[]):
        self.connection = connection
        self.name = name
        self.type = type
        self.space_id = space_id
        self._space = None
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
                  space_id=data.get('space_id'),
                  streams=data.get('streams'))
        return obj

    def space(self):
        if self._space is None and self.space_id is not None:
            # Find the Space
            self._space = self.connection.get_space(self.space_id)
        return self._space

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

    def persisted(self):
        return self.id is not None

    def save(self):
        if self.persisted():
            self.connection.update_chart(self, self.space())
        else:
            dummy = self.connection.create_chart(self.name, self.space(), streams=self.streams)
            self.id = dummy.id

    def rename(self, new_name):
        self.name = new_name
        self.save()

    def delete(self):
        return self.connection.delete_chart(self.id, self.space_id)
