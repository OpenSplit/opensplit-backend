#! /usr/bin/env python3
from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from models import User, Session
from flask_restful import Resource, Api, reqparse
from helper import authenticate, generate_session_key

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


@auth.verify_password
def verify_password(token, nope):
    user = User.verify_auth_token(token)
    if not user:
        return False
    g.user = user
    return True


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
