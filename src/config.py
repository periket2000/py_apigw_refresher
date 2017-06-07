import os

config_dir = os.getenv('CONFIG_DIR', os.path.dirname(os.path.realpath(__file__)))
apigw_config_dir = os.getenv('APIGW_CONFIG_DIR', os.path.dirname(os.path.realpath(__file__)))
tmp_dir = os.getenv('TMP_DIR', '/tmp')
tgz_mime_type = 'application/tar+gzip'
zip_fic = 'config.tgz'
config_fic = 'config.json'
