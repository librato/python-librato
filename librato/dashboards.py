from .instruments import Instrument


class Dashboard(object):
    """Librato Dashboard Base class"""

    def __init__(self, connection, name, id=None, instruments=[]):
        self.connection = connection
        self.name = name
        self.instruments = []
        for i in instruments:
            self.add_instrument(i)
        self.id = id

    @classmethod
    def from_dict(cls, connection, data):
        """
        Returns a Dashboard object from a dictionary item,
        which is usually from librato's API
        """
        obj = cls(connection,
                  data['name'],
                  instruments=data['instruments'],
                  id=data['id'])
        return obj

    def get_payload(self):
        return {'name': self.name,
                'instruments': [x.id for x in self.instruments]}

    def add_instrument(self, instrument):
        if isinstance(instrument, Instrument):
            self.instruments.append(instrument)
        # We should handle this better, i.e. allowing instrument instantiation from integers, for consistency.
        elif isinstance(instrument, int):
            # Aaah, cascading GETs!
            instrument = self.connection.get_instrument(instrument)
            # get_instrument throws a librato.exceptions.NotFound: [404] request: Not Found
            self.instruments.append(instrument)

    def save(self):
        self.connection.update_dashboard(self)
