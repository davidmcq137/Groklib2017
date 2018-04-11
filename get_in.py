def get_in(d, keylist):
  if not d:
    return None
  if not keylist:
    return d
  return get_in(d.get(keylist[0]), keylist[1:])
  
  
testdict =   {"foo": {"bar": 2}}
print(get_in(testdict, ["foo", "bar"]))
print(get_in(testdict, ["not", "here"]))
