# outgrew this piece of shit before i even launched
# thank god i cerntralized the db logic early, it means that switching to a real db won't break the business logic
# import pickledb
# db: pickledb.PickleDB =pickledb.load("platform.db.json", False)

import json
from bson.objectid import ObjectId
import pymongo
from credentials import secrets

#behold, a real db. to get up and running, run the install.py script to generate credentials module based on the secrets you give it
#and then it initializes your database with some helpful defaults...  
client = pymongo.MongoClient(secrets["mongo"])
db = client.synthia_core


def select(table_name, query):
    return list(db[table_name].find(query))


def select_all(table_name, get_values=True):
    return list(db[table_name].find())
    if get_values:
        return [db.get(k) for k in filter(lambda key: key.startswith(table_name), db.getall())]
    else:
        return [unpack_key(k) for k in filter(lambda key: key.startswith(table_name), db.getall())]


def get_item(item_key, table_name=""):
    if item_key is str:
        item_key = {'_id': ObjectId(item_key)}
    return db[table_name].find_one(item_key)

    return db.get(pack_key(item_key, table_name=table_name))


def upsert(item_key, table_name="", item_value=None):
    if item_key is str:
        item_key = {'_id': ObjectId(item_key)}
    return db[table_name].update_one(item_key, {'$set': item_value}, upsert=True)

    result = db.set(k, item_value)
    db.dump()
    return result
    # db.("platform.db.json")


# let's get some structure around this damn replit db
# otherwise every module will be full of x = db["x"] or x_default
def get_or_create(item_key, table_name="", default_value=None):
    if item_key is str:
        item_key = {'_id': ObjectId(item_key)}

    if (db[table_name].count_documents(item_key) == 0):
        db[table_name].insert_one(default_value)

    return db[table_name].find_one(item_key)

    k = pack_key(item_key, table_name=table_name)
    if not db.get(k):
        db.set(k, default_value)
        db.dump()

    return db.get(k)  # sanity check to make sure the item was


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
