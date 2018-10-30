import os
from flask import Flask, request, Response, send_from_directory
from api_blueprints.config import update_config
import src.config as config
import json
from py_blueprints.test_endpoint.blueprint import blueprint as testbp

app = Flask(__name__)
app.register_blueprint(update_config)
app.register_blueprint(testbp)

welcome = """
API GATEWAY REFRESHER.

@endpoints = /config    [GET]: get config for the api gateway.
           = /update    [PUT]: update the mapping configuration of the aplication "config.json"
           = /endpoints [GET]: get the endpoints for all the applications
           = /mappings  [GET]: get the current mapping configuration
"""

# SCHEDULER should be one of [aurora, marathon]
scheduler = os.getenv('SCHEDULER', 'aurora')
if 'aurora' == scheduler:
    from aurora_refresher import Tasks

if 'marathon' == scheduler:
    from refresher import Tasks

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
