import connectors.utils as dbutils
def get_model(model_id):
  return dbutils.get_item(model_id, "chat_models")

def list_models(include_nsfw=False):
  return [m for m in dbutils.select_all("chat_models", get_values=False)]

def populate_base_models(models_dict):
  model_keys= models_dict.keys()
  for k in model_keys:
    models_dict[k]["owner"] = "admin"
    models_dict[k]["_id"] = k
    dbutils.upsert(k, "chat_models", models_dict[k])
    
def backup_base_models(models_dict, file="connectors/data/base_models.json"):
  dbutils.save_json(models_dict, file)

def restore_base_models(file="connectors/data/base_models.json"):
  models_dict = dbutils.load_json(file)
  populate_base_models(models_dict)

