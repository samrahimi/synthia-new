from flask import Flask, render_template, jsonify, request
import connectors.session as sessions, connectors.models as models, connectors.users as users, connectors.utils as db

#from connectors.models import get_model, list_models
#from connectors.users import login, is_logged_in, get_logged_in_user, get_user
#from connectors.prompts import Session

app = Flask(__name__)


@app.route('/')
def index():
  return render_template("index.html")


@app.route('/models', methods=["GET"])
def get_models():
  return jsonify (models.list_models(include_nsfw = True))
  #return jsonify(allkeys)

@app.route('/models/<model_id>', methods=["GET"])
def get_model(model_id):
  return jsonify(models.get_model(model_id))

@app.route('/users/signup', methods=["POST"])
def signup(data):
  u = users.signup(user_id=data["user_id"], name=data["name"], access_level="trial", email=data["email"], password=data["password"])
  if not u:
    return {"error":"user already exists or an error occured, pls retry"}
  else:
    return jsonify(users.serialize_user(u))

@app.route('/users/login', methods=["POST"])
def do_login(data):
  u = users.login(data["user_id"], data["password"])
  if u:
    return users.serialize_user(u)
  else:
   return {"error":"incorrect user id or password"}


@app.route('/sessions/create', methods=["POST"])
def create_session(data):
  #import json
  #req = json.loads(data0)
  req = data
  print("new session for "+req["user_id"])
  uid = req["user_id"]
  modelid = req["model_id"]
  
  session= sessions.Session(model_id=modelid, user_id=req["user_id"], user_name=req["user_name"], ai_name=req["ai_name"])
  return session.save()
  #note: the Session constructor will update the in-memory sessions collections that are referenced by the User object
  #so the new session will appear in the user's sessions (we fucking hope so, anyways)

app.run(host='0.0.0.0', port=8080)

