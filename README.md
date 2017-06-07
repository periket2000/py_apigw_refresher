# Python project for generating nginx api gw upstream servers for mesos

## Running the application
1. export PYTHONPATH=$PWD
2. python src/app.py

## Overwrite app configuration (mappings)
1. curl --upload-file new_config.json http://host:port/update
