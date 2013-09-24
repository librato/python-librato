
class Instrument(object):
    """Librato Instrument Base class"""

    def __init__(self, connection, name, id=None, streams=[], attributes={}, description=None):
        self.connection = connection
        self.name = name
        self.streams = []
        for i in streams:
            if isinstance(i, Stream):
                self.streams.append(i)
            elif isinstance(i, dict):  # Probably parsing JSON here
                self.streams.append(Stream(i['metric'], i['source']))
            else:
                self.streams.append(Stream(*i))
        self.attributes = attributes
        self.id = id

    @classmethod
    def from_dict(cls, connection, data):
        """Returns a metric object from a dictionary item,
        which is usually from librato's API"""
        obj = cls(connection,
                  data['name'],
                  streams=data['streams'],
                  id=data['id'],
                  attributes=data['attributes'])
        return obj

    def get_payload(self):
        return {'name': self.name,
                'attributes': self.attributes,
                'streams': [x.get_payload() for x in self.streams]}

    def new_stream(self, metric, source='*'):
        stream = Stream(metric, source)
        self.streams.append(stream)
        return stream

    def save(self):
        self.connection.update_instrument(self)


class Stream(object):
    def __init__(self, metric, source='*'):
        self.metric = metric
        self.source = source

    def get_payload(self):
        return {'metric': self.metric,
                'source': self.source}
