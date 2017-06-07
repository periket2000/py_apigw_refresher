import os
from refresher import Tasks
from flask import Flask, request, Response, send_from_directory
from api_blueprints.config import update_config
import src.config as config

app = Flask(__name__)
app.register_blueprint(update_config)

welcome = """
API GATEWAY REFRESHER.

@endpoints = /config [GET]: get config for the api gateway.
           = /update [PUT]: update the configuration of the aplication "config.json"
"""

@app.route('/')
def hello_world():
    return Response(welcome, mimetype="text/plain")

def generate_tgz():
    t = Tasks()
    return t.generate(generate_zip=True)

@app.route('/config')
def stream_config():
    result, _ = generate_tgz()
    if result:
        return send_from_directory(config.apigw_config_dir, config.zip_fic, as_attachment=True, mimetype=config.tgz_mime_type)
    else:
        return Response('Nothing generated', mimetype="text/plain")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=9090)
