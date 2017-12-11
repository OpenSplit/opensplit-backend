#! /usr/bin/env python3
from flask_restful import Resource, reqparse, abort
from opensplit import api, db
from flask import g
from opensplit.models import User, Session
from opensplit.helper import authenticate, generate_session_key

user_post_parser = reqparse.RequestParser()
user_post_parser.add_argument('email')


class UserResource(Resource):

    @authenticate
    def get(self):
        return {"id": g.user.id,
                "email": g.user.email}

    def post(self):
        args = user_post_parser.parse_args()
        u = User(email=args["email"])
        db.session.add(u)
        db.session.commit()
        return {"userid": u.id}


login_parser = reqparse.RequestParser()
login_parser.add_argument('userid')


class LoginResource(Resource):
    def get(self, email):
        """
        Generate a new login token
        """
        user = User.query.filter_by(email=email).first()
        if user:
            token = user.generate_login_token().decode()
            print("#"*10)
            print("> Generated new logintoken for '{}'".format(user.email))
            print("> {}".format(token))
            print("#"*10)
            return {"userid": user.id}
        else:
            abort(500)


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
            return {"session_key": session_key}
        else:
            abort(500)


api.add_resource(UserResource, '/user')
api.add_resource(LoginResource, '/login/<string:email>')
api.add_resource(SessionResource, '/session/<string:login_token>')
