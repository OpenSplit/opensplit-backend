#! /usr/bin/env python3
from flask import Flask, g
from flask_restful import Resource, Api, reqparse, abort, request
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask_httpauth import HTTPBasicAuth
from functools import wraps
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = "oibi9Fi2da5hahkoonoo"

# Flask-RESTful
api = Api(app)

# SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# HTTPAuth
auth = HTTPBasicAuth()

def authenticate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        session_key = request.headers.get("Authorization", None)
        if session_key:
            print("Got auth header")
            session = Session.query.filter_by(session_key=session_key).one()
            if session:
                print("Found valid session for this key")
                return func(*args, **kwargs)
            else:
                print("can't find a valid session for this key")
                abort(401)
        else:
            print("No auth header")
            abort(401)
    return wrapper

def generate_session_key():
    # Code stolen from Django Project
    allowed_chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    length = 50
    return ''.join(random.choice(allowed_chars) for i in range(length))


@auth.verify_password
def verify_password(token, nope):
    user = User.verify_auth_token(token)
    if not user:
        return False
    g.user = user
    return True

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    sessions = db.relationship('Session', backref='user', lazy=True)

    def generate_login_token(self, expiration = 600):
        s = Serializer(app.config['SECRET_KEY'], expires_in = expiration)
        return s.dumps({ 'id': self.id})

    @staticmethod
    def verify_login_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None # valid token, but expired
        except BadSignature:
            return None # invalid token
        user = User.query.get(data['id'])
        return user


class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_key = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


user_post_parser = reqparse.RequestParser()
user_post_parser.add_argument('email')


class UserResource(Resource):
    method_decorators = [authenticate]

    def get(self):
        user = User.query.all()
        return {"user": [u.id for u in user]}

    def post(self):
        args = user_post_parser.parse_args()
        u = User(email=args["email"])
        db.session.add(u)
        db.session.commit()
        return {"userid": u.id}


login_parser = reqparse.RequestParser()
login_parser.add_argument('userid')


class LoginResource(Resource):
    def get(self, user_id):
        """
        Generate a new login token
        """
        user = User.query.get(user_id)
        if user:
            token = user.generate_login_token().decode()
            print(token)
            return token

class SessionResource(Resource):
    def get(self, login_token):
        """
        Generate a new session
        """
        user = User.verify_login_token(login_token)
        if user:
            # return "valid token for userid {}".format(user.id)
            session_key = generate_session_key()
            s = Session(user=user, session_key=session_key)
            db.session.add(s)
            db.session.commit()
            return session_key
        else:
            return "invalid token"


api.add_resource(UserResource, '/user', '/users/<int:user_id>')
api.add_resource(LoginResource, '/login/<int:user_id>')
api.add_resource(SessionResource, '/session/<string:login_token>')


if __name__ == '__main__':
    app.run(debug=True)
