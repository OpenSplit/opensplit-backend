#! /usr/bin/env python3
from flask import Flask
from flask_restful import Resource, Api, reqparse
from flask_cors import CORS
from opensplit.database import db_session

app = Flask(__name__)
app.config['SECRET_KEY'] = "oibi9Fi2da5hahkoonoo"

CORS(app)

# Flask-RESTful
api = Api(app)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

import opensplit.views
