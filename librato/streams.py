class Stream(object):
    def __init__(self, metric=None, source='*', composite=None,
                 group_function=None, summary_function=None,
                 transform_function=None, downsample_function=None,
                 period=None, id=None, type=None):
        self.metric = metric
        self.composite = composite
        self.source = source
        # average, sum, min, max, breakout
        self.group_function = group_function
        # average, sum, min, max, count (or derivative if counter)
        self.summary_function = summary_function
        self.transform_function = transform_function
        self.downsample_function = downsample_function
        self.period = period
        self.type = type
        if self.composite:
            self.source = None

    def get_payload(self):
        payload = {
            'metric': self.metric,
            'source': self.source
        }
        attrs = ['composite', 'period', 'group_function', 'summary_function']
        for attr in attrs:
            if getattr(self, attr) is not None:
                payload[attr] = getattr(self, attr)
        return payload
