from flask import Blueprint, Response, request
import src.config as config
import os
import datetime

update_config = Blueprint('update_config', __name__)

def backup():
    backup_file = config.config_dir + "/" + config.config_fic + "." + str(datetime.date.today()) + ".bck"
    os.rename(config.config_dir + "/" + config.config_fic, backup_file)
    return backup_file

def restore(filename):
    os.rename(filename, config.config_dir + "/" + config.config_fic)
    

@update_config.route('/update', methods=['PUT'])
def update():
    backup_file = backup()
    try:
        with open(config.config_dir + "/" + config.config_fic, 'w') as f:
            f.write(request.stream.read().decode('utf-8'))
        return Response("Configuration updated", mimetype="text/plain")
    except:
        restore(backup_file)
        return Response("Exception raised, nothing updated.", mimetype="text/plain")
