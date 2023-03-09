from flask import Flask, render_template, jsonify, request
import connectors.session as sessions, connectors.models as models, connectors.users as users, connectors.utils as db
import json
import plugins.commands as cmd

#from connectors.models import get_model, list_models
#from connectors.users import login, is_logged_in, get_logged_in_user, get_user
#from connectors.prompts import Session
#utility
def get_viewmodel(user_id):
  if (users.is_logged_in(user_id=user_id)):
    return users.serialize_user(users.get_logged_in_user(user_id = user_id))
  else:
    u= users.get_user(user_id, include_sessions=True)
    if u:
      return users.serialize_user(u)

app = Flask(__name__)

@app.route("/api")
def get_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        # Parse the rule into a dict of the path and methods
        route = {
            'path': rule.rule,
            'methods': list(rule.methods)
        }
        # Add the expected parameters for the route
        params = []
        for arg in rule.arguments:
            params.append(arg)
        route['params'] = params

        routes.append(route)

    return jsonify(routes)

@app.route("/")
def redirect_to_splash():
  return render_template("index.html")
#the following API lets you login, signup, create new sessions with any model, get session state, send a message to gpt, and view the response
#TODO: clone / edit / create new models, security for logins, buy credits, handle multimodal chains like @@DRAW
@app.route('/www/login')
def show_login_screen():
  return render_template("login.html")


#this is the main screen
#we need to enforce the login much better than currently
@app.route('/www/interactions/<user_id>')
def interact(user_id):
  return render_template("chat_bs.html", header_text="Fuck CSS", user=get_viewmodel(user_id))

@app.route('/www/models', methods=["GET"])
def all_models():
  all=[]
  for m in models.list_models(include_nsfw = True):
    model = models.get_model(m)
    del model["_id"]
    all.append(model)
  return render_template("models.html", models=all, user_id=request.args.get("user_id"))

  return jsonify (all_models)
  #return jsonify(allkeys)

@app.route('/www/edit_model/<model_id>', methods=["GET"])
def model_details(model_id):
  m = models.get_model(model_id)
  del m["_id"]
  return render_template("model_studio.html", model=m, user_id=request.args.get("user_id"))

@app.route('/www/create_model', methods=["GET"])
def model_create():
  return render_template("model_studio.html", model={}, user_id=request.args.get("user_id"))


@app.route('/model/save', methods=["POST"])
def save_model():
  newmodel = {
    "owner": request.form['owner'],
    "invocation": request.form["invocation"] if "invocation" in request.form else "",
    "model_description": request.form["model_description"] if "model_description" in request.form else "",
    "default_session_context": request.form["default_session_context"] if "default_session_context" in request.form else "",
    "openai_settings": eval(request.form["openai_settings"]),
    "training_examples": request.form["examples"] if "examples" in request.form else ""
  }
  import connectors.utils as dbutils
  dbutils.upsert({"model_id": request.form["model_id"]},"chat_models", 
                       newmodel)
  from flask import redirect
  return redirect("/www/interactions/"+request.form["owner"]+"?model_saved=true")

  
  

@app.route('/models', methods=["GET"])
def get_models():
  return jsonify (models.list_models(include_nsfw=True))


@app.route('/models/<model_id>', methods=["GET"])
def get_model(model_id):
  m = models.get_model(model_id)
  del m["_id"]
  return jsonify(m)

@app.route('/users/signup', methods=["POST"])
def signup():
  data = json.loads(request.get_data(as_text=True))
  u = users.signup(user_id=data["user_id"], name=data["name"], access_level="trial", email=data["email"], password=data["password"])
  if u is not None:
    return users.serialize_user(u)
  else:
    return {"error":"user already exists or an error occured, pls retry"}
  

@app.route('/users/login', methods=["POST"])
def do_login():
  data = json.loads(request.get_data(as_text=True))

  u = users.login(data["user_id"], data["password"])
  if u:
    return users.serialize_user(u)
  else:
   return {"error":"incorrect user id or password"}

@app.route('/sessions/spawn', methods=["POST"])
def create_session():
  req = json.loads(request.get_data(as_text=True))

  #import json
  #req = json.loads(data0)
  print("begin spawning process for owner "+req["user_id"])
  #like many animals and plants, bots can reproduce sexually or asexually
  session= sessions.Session(model_id=req["model_id"], user_id=req["user_id"], user_name=req["user_name"], ai_name=req["ai_name"], is_existing= False)
  if "dna" in req:
      daddy_dna = req["dna"]
      daddy= req["father"]

      session.add_male_dna(daddy_dna, parent_uid=req["daddy"], include_default=True, identity_note=None)

  #the session has autosaved upon creation, so loading the relevant user will also load the new session
  #its ineffecient but right now its more sane than trying to synchronize in-memory dicts with persistant storage
  return users.serialize_user(users.get_user(user_id=req["user_id"], include_sessions=True)) #to see if it works, and to allow the client side to just refresh the list instead of having to append

# unnecessary: session state is autosaved when anything changes, and refreshed when you load a user
# @app.route("/users/<user_id>/save_state", methods=["GET"])
# def save_state(user_id):
#   return users.save_state(user_id) if users.is_logged_in(user_id) else {"error": "this only works for logged in users"}


@app.route('/users/refresh/<user_id>', methods=["GET"])
def refresh(user_id):
    u= users.get_user(user_id, include_sessions=True)
    if u:
      return users.serialize_user(u)
    
@app.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
  if (users.is_logged_in(user_id=user_id)):
    return users.serialize_user(users.get_logged_in_user(user_id = user_id))
  else:
    u= users.get_user(user_id, include_sessions=True)
    if u:
      return users.serialize_user(u)

@app.route("/sessions/<session_id>/query/<message_to_gpt>", methods=["GET"])
def perform_inference(session_id, message_to_gpt):
  the_session: sessions.Session = sessions.Session.load(session_id) #sessions.sessions["by_id"][session_id]
  response = the_session.ask_gpt(message = message_to_gpt)
  reply = cmd.parse(response) if response else "error"
  return {"response": reply} 

#if this all works, I am sincerely surprised :)
app.run(host='0.0.0.0', port=8080)

