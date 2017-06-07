import os
from refresher import Tasks
from flask import Flask, request, Response, send_from_directory
app = Flask(__name__)

config_dir = os.getenv('APIGW_CONFIG_DIR', os.path.dirname(os.path.realpath(__file__)))
mime_type = 'application/tar+gzip'
fic = 'config.tgz'

welcome = """
API GATEWAY REFRESHER.

@endpoints = /config : get config for the api gateway.
"""

@app.route('/')
def hello_world():
    return Response(welcome, mimetype="text/plain")

def generate_tgz():
    t = Tasks()
    return t.generate()

@app.route('/config')
def stream_config():
    result, _ = generate_tgz()
    if result:
        return send_from_directory(config_dir, fic, as_attachment=True, mimetype=mime_type)
    else:
        return Response('Nothing generated', mimetype="text/plain")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=9090)
