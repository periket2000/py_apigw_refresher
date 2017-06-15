import os
from refresher import Tasks
from flask import Flask, request, Response, send_from_directory
from api_blueprints.config import update_config
import src.config as config
import json

app = Flask(__name__)
app.register_blueprint(update_config)

welcome = """
API GATEWAY REFRESHER.

@endpoints = /config    [GET]: get config for the api gateway.
           = /update    [PUT]: update the mapping configuration of the aplication "config.json"
           = /endpoints [GET]: get the endpoints for all the applications
           = /mappings  [GET]: get the current mapping configuration
"""

@app.route('/')
def landing():
    return Response(welcome, mimetype="text/plain")

@app.route('/mappings')
def stream_mappings():
    t = Tasks()
    val = t.mappings()
    if val:
        return Response(json.dumps(val), mimetype="application/json")
    else:
        return Response('Nothing generated', mimetype="text/plain")

@app.route('/endpoints')
def stream_endpoints():
    t = Tasks()
    result, val = t.endpoints()
    if result:
        return Response(str(val), mimetype="text/plain")
    else:
        return Response('Nothing generated', mimetype="text/plain")

@app.route('/config')
def stream_config():
    t = Tasks()
    result, val = t.generate()
    if result:
        return Response(str(val), mimetype="text/plain")
    else:
        return Response('Nothing generated', mimetype="text/plain")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=9090)
