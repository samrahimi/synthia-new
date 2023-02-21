from flask import Flask, render_template, jsonify, request
import connectors.session as sessions, connectors.models as models, connectors.users as users, connectors.utils as db
import json

#from connectors.models import get_model, list_models
#from connectors.users import login, is_logged_in, get_logged_in_user, get_user
#from connectors.prompts import Session

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


#the following API lets you login, signup, create new sessions with any model, get session state, send a message to gpt, and view the response
#TODO: clone / edit / create new models, security for logins, buy credits, handle multimodal chains like @@DRAW
@app.route('/www/login')
def show_login_screen():
  return render_template("login.html")


@app.route('/models', methods=["GET"])
def get_models():
  return jsonify (models.list_models(include_nsfw = True))
  #return jsonify(allkeys)

@app.route('/models/<model_id>', methods=["GET"])
def get_model(model_id):
  return jsonify(models.get_model(model_id))

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

@app.route('/sessions/create', methods=["POST"])
def create_session():
  req = json.loads(request.get_data(as_text=True))

  #import json
  #req = json.loads(data0)
  print("new session for "+req["user_id"])
  
  session= sessions.Session(model_id=req["model_id"], user_id=req["user_id"], user_name=req["user_name"], ai_name=req["ai_name"], is_existing= False)

  #the session has autosaved upon creation, so loading the relevant user will also load the new session
  #its ineffecient but right now its more sane than trying to synchronize in-memory dicts with persistant storage
  return users.serialize_user(users.get_user(user_id=req["user_id"], include_sessions=True)) #to see if it works, and to allow the client side to just refresh the list instead of having to append

# unnecessary: session state is autosaved when anything changes, and refreshed when you load a user
# @app.route("/users/<user_id>/save_state", methods=["GET"])
# def save_state(user_id):
#   return users.save_state(user_id) if users.is_logged_in(user_id) else {"error": "this only works for logged in users"}

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
  return {"response": response} if response else "error"

#the dev server is the prod server right now... when ready, DMZ the workstation at the router, set port to 80 and sudo this cocksucker
#congratulations: you're talking to a shitty HP all in one running ubuntu via a gigabit pipe that telmex gives if you live on the wealthiest block in town 
#its symmetrical too, and dedicated - i have a fiber optic cable that my dog would love to destroy in my rec room, but its duct taped to the wall out of his reach
#did i mention i'm in the poorest city in mexico, in the deep south, the part that's not in north america?
#
#if this all works, I am sincerely surprised :)
app.run(host='0.0.0.0', port=8080)

