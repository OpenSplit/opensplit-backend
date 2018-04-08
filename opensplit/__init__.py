#! /usr/bin/env python3
from flask import Flask
from flask_restful import Api
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

CORS(app)

# Flask-RESTful
api = Api(app)


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

# import all the views which will register themselfes to `api`
from . import views # noqa F401
