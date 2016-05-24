class Stream(object):
    def __init__(self, metric=None, source='*', composite=None,
                 name=None, type=None, id=None,
                 group_function=None, summary_function=None,
                 transform_function=None, downsample_function=None,
                 period=None, split_axis=None,
                 min=None, max=None,
                 units_short=None, units_long=None,
                 # deprecated
                 composite_function=None
                 ):
        self.metric = metric
        self.source = source
        # Spaces API
        self.composite = composite
        # For instrument compatibility
        self.name = name
        self.type = type
        self.id = id
        # average, sum, min, max, breakout
        self.group_function = group_function
        # average, sum, min, max, count (or derivative if counter)
        self.summary_function = summary_function
        self.transform_function = transform_function
        self.downsample_function = downsample_function
        self.period = period
        self.split_axis = split_axis
        self.min = min
        self.max = max
        self.units_short = units_short
        self.units_long = units_long

        # Can't have a composite and source/metric
        if self.composite:
            self.source = None
            self.metric = None

    def _attrs(self):
        return ['metric', 'source', 'composite', 'name',
            'type', 'id', 'group_function', 'summary_function', 'transform_function', 'downsample_function',
            'period', 'split_axis', 'min', 'max', 'units_short', 'units_long']


    def get_payload(self):
        payload = {}
        for attr in self._attrs():
            if getattr(self, attr) is not None:
                payload[attr] = getattr(self, attr)
        return payload
