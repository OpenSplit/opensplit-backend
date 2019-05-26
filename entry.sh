#! /bin/sh
set -eu
export FLASK_APP="run.py"

# Apply latest database migrations
pipenv run flask db upgrade

# Start Gunicorn
pipenv run gunicorn -w 2 -b 0.0.0.0:5000 run:app
