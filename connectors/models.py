import connectors.utils as dbutils
models_dict = {}

def get_model(model_id):
  return dbutils.get_item({"model_id":model_id}, "chat_models")

def list_models(include_nsfw=False):
  return [m["model_id"] for m in dbutils.select_all("chat_models", get_values=True)]

def populate_base_models(models_dict):
  model_keys= models_dict.keys()
  for k in model_keys:
    models_dict[k]["owner"] = "admin"
    models_dict[k]["model_id"] = k
    dbutils.upsert({"model_id": k}, "chat_models", models_dict[k])
    
def backup_base_models(models_dict, file="connectors/data/base_models.json"):
  dbutils.save_json(models_dict, file)

def restore_base_models(file="connectors/data/base_models.json"):
  models_dict = dbutils.load_json(file)
  populate_base_models(models_dict)

