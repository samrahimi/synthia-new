#from replit import db
#replit db is awful, mangling my dicts
#that is why you centralize database logic in a module like this one
# so you can just go

import pickledb
db=pickledb.load("platform.db", True)

#and with some very small changes the whole app is migrated over

def pack_key(item_key, table_name=""):
  '''and... this is why i don't like nosql databases, because you gotta do shit like this'''
  full_key = f"{table_name}.{item_key}" if len(table_name) > 0 else item_key
  return full_key


def unpack_key(full_key: str):
  if full_key.count(".") == 0:
    return full_key
  unpacked_key = full_key.split(".")
  #i don't think we need to return the table name but its unpacked_key[0] if that changes
  return unpacked_key[1]


def select_all(table_name, get_values=True):
  if get_values:
    return [{unpack_key(k): db.get(k)} for k in filter(lambda key: key.startswith(table_name), db.getall())]
  else:
    return [unpack_key(k) for k in filter(lambda key: key.startswith(table_name), db.getall())]


def get_item(item_key, table_name=""):
  return db.get(pack_key(item_key, table_name=table_name))


def upsert(item_key, table_name="", item_value=None):
  k = pack_key(item_key, table_name=table_name)
  return db.set(k, item_value)


#let's get some structure around this damn replit db
#otherwise every module will be full of x = db["x"] or x_default
def get_or_create(item_key, table_name="", default_value=None):
  k = pack_key(item_key, table_name=table_name)
  if not db.get(k):
    db.set(k, default_value)
  
  return db.get(k) # sanity check to make sure the item was 


import json

def load_json(filename):
  with open(filename) as file:
    data = json.load(file)
  return json.loads(data)

def save_json(object,  filename):
  data = json.dumps(object)
  with open(filename, 'w') as outfile: 
    json.dump(data, outfile)

'''turn a dictionary into a normal object'''
def dict_to_object(d):
    if isinstance(d, list):
        d = [dict_to_object(x) for x in d]
    if not isinstance(d, dict):
        return d
    class C(object):
        pass
    o = C()
    for k in d:
        o.__dict__[k] = dict_to_object(d[k])
    return o


'''deep copy of an object'''


def deep_copy(obj):
    if isinstance(obj, list):
        return [deep_copy(x) for x in obj]
    if isinstance(obj, dict):
        return {k: deep_copy(obj[k]) for k in obj.keys()}
    return obj
