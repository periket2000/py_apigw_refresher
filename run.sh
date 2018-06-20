export PYTHONPATH=./src
gunicorn --workers 4 --timeout 120 --bind 0.0.0.0:9090 app:app
