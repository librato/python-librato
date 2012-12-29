class Measurement(object):
  def __init__(self, value, name=None, source=None, measure_time=None):
    self.value        = value
    self.name         = name
    self.source       = source
    self.measure_time = measure_time
