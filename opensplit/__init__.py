#! /usr/bin/env python3
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api, reqparse
from flask_restful.utils import cors

app = Flask(__name__)
app.config['SECRET_KEY'] = "oibi9Fi2da5hahkoonoo"

app.decorators=[cors.crossdomain(origin='*')]

# Flask-RESTful
api = Api(app)

# SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

import opensplit.views
