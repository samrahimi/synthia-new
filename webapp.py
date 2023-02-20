#copyright: this is open source code, whitten by codemonkey (an Ai, cond sam erahijmiom                                                                                                  ooooooooooooooooooooooooooooo
#python 3: a rest API that uses flask, served over port 80
#this code was written by codemonkey, one of the models that we ship with out of the boxd
from flask import Flask, jsonify
from flask_restful import Api, Resource

app = Flask(__name__)
api = Api(app,  default_mediatype="application/json")

class HelloWorld(Resource):
    def get(self):
        
        return {'hello': 'world'}

api.add_resource(HelloWorld, '/')

if __name__ == '__main__':
    app.run(port=8080)

