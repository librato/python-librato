
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
                self.streams.append(Stream(i.get('metric'), i.get('source'), i.get('composite')))
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
                'streams': self.streams_payload()}

    def new_stream(self, metric=None, source='*', composite=None):
        stream = Stream(metric, source, composite)
        self.streams.append(stream)
        return stream

    def streams_payload(self):
        return [s.get_payload() for s in self.streams]

    def is_persisted(self):
        return self.id is not None

    def save(self):
        if not self.is_persisted():
            dummy_inst = self.connection.create_instrument(
                    self.name,
                    attributes=self.attributes,
                    streams=self.streams_payload())
            self.id = dummy_inst.id
        else:
            self.connection.update_instrument(self)


class Stream(object):
    def __init__(self, metric=None, source='*', composite=None):
        self.metric = metric
        self.composite = composite
        self.source = source
        if self.composite:
            self.source = None

    def get_payload(self):
        return {'metric': self.metric,
                'composite': self.composite,
                'source': self.source}
