import connectors.utils as dbutils
models_dict = {}

def get_model(model_id):
  return dbutils.get_item({"model_id":model_id}, "chat_models")

def list_models(include_nsfw=False):
  return [m["model_id"] for m in dbutils.select_all("chat_models", get_values=True)]

#clone a model, assigning a new id and owner
#todo: implement a mutation function that tweaks elements of the static context
#by varying base model inference settings or rewriting instructions and examples
#using another model... it should operate according to the mutation rate
#but should not be implemented until there is a large number of users
#spawning new models, so that we can measure and optimize the evolutionary process
def reproduce(mutation_rate=0.05, user_id="", parent_id="super_gpt", new_id="baby_g"):
  original = get_model(parent_id)

  #check: is id available
  if get_model(new_id):
    print("Error: model id is taken, try again")
    return None
  else:
    new_model = dbutils.deep_copy(original) 
    new_model["model_id"] = new_id
    new_model["parent_id"] = parent_id
    new_model["owner"] = user_id
    dbutils.upsert({"model_id": new_id}, "chat_models", new_model)
    return new_model

def update(invocation="", model_id="", training_examples = [], default_session_context=""):
  dbutils.upsert({"model_id": model_id},"chat_models", {"training_examples": training_examples, "default_session_context": default_session_context, "invocation": invocation})

def create_new(user_id="", invocation="", model_id="", training_examples = [], default_session_context=""):
  if (get_model(model_id)):
    print("Model ID taken, choose another or call update")
    return None
  return dbutils.upsert({"model_id": model_id},"chat_models", {"owner": user_id, "training_examples": training_examples, "default_session_context": default_session_context, "invocation": invocation})

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

