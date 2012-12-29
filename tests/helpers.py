"""tell me if two dics have the same contents """
def dicts_match(x, truth):
  shared_items              = set(x.items()) & set(truth.items())
  same_length               = len(x) == len(truth)
  same_overlap_shared_items = len(shared_items) == len(truth)
  if same_length and same_overlap_shared_items:
    return True
  else:
    print "--x:     "; print json.dumps(x)
    print "--truth: "; print json.dumps(truth)
    return False
