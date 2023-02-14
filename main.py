from flask import Flask, render_template, jsonify, request
from connectors.session import Session, models, sessions

#from connectors.prompts import Session
'''
app = Flask(__name__)


@app.route('/')
def index():
  return render_template("index.html")


@app.route('/models', methods=["GET"])
def get_models():
  allkeys = [str(key) for key in models.keys()]
  return jsonify(allkeys)


@app.route('/sessions/create', methods=["POST"])
def create_session():
  request.query_string


app.run(host='0.0.0.0', port=8080)
'''

sesh = Session(model_id="super_gpt",
               user_id="sammy",
               user_name="Sam",
               ai_name="Super G")
while True:
  query = input(">>>>>")
  response = sesh.ask_gpt(query)
  print("Super G says: " + response)
