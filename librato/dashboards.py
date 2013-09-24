
class Dashboard(object):
    """Librato Dashboard Base class"""

    def __init__(self, connection, name, id=None, instrument_dicts=None):
        self.connection = connection
        self.name = name
        self.instrument_ids = []
        self._instruments = None
        for i in (instrument_dicts or []):
            self.instrument_ids.append(i['id'])
        self.id = id

    @classmethod
    def from_dict(cls, connection, data):
        """
        Returns a Dashboard object from a dictionary item,
        which is usually from librato's API
        """
        obj = cls(connection,
                  data['name'],
                  instrument_dicts=data['instruments'],
                  id=data['id'])
        return obj

    def get_payload(self):
        return {'name': self.name,
                'instruments': self.instrument_ids[:]}

    def get_instruments(self):
        if self._instruments is None:
            instruments = []
            for i in self.instrument_ids:
                instruments.append(self.connection.get_instrument(i))
            self._instruments = instruments

        return self._instruments[:]

    def save(self):
        self.connection.update_dashboard(self)
