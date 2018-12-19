export FLASK_APP="run.py"

# Apply latest database migrations
pipenv run flask db upgrade

# Start Gunicorn
pipenv run gunicorn -w 2 -b 127.0.0.1:5000 run:app
