from replit import db


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
    return [{unpack_key(k): db[k]} for k in db.prefix(table_name)]
  else:
    return [unpack_key(k) for k in db.prefix("table_name")]


def get_item(item_key, table_name=""):
  return db[pack_key(item_key, table_name=table_name)]


def upsert(item_key, table_name="", item_value=None):
  k = pack_key(item_key, table_name=table_name)
  db[k] = item_value


#let's get some structure around this damn replit db
#otherwise every module will be full of x = db["x"] or x_default
def get_or_create(item_key, table_name="", default_value=None):
  k = pack_key(item_key, table_name=table_name)
  if k not in db.keys():
      db[k] = default_value
  return db[k]
