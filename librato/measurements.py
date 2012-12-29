class Measurement(object):
  """Models a measurement.
  name         : we will always have a value for that param (metric name by default)
  value        : value of the measurement
  measure_time : OPTIONAL. unix timestamp.
  source       : OPTIONAL
  """
  def __init__(self, value, name, source=None, measure_time=None):
    self.value        = value
    self.name         = name
    if source:
      self.source = source
    if measure_time:
      self.measure_time = measure_time
