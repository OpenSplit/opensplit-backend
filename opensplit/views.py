#! /usr/bin/env python3
from flask_restful import Resource, reqparse, abort
from opensplit import api
from opensplit.database import db_session
from flask import g
from opensplit.models import User, Session, Group
from opensplit.helper import authenticate, generate_session_key

user_post_parser = reqparse.RequestParser()
user_post_parser.add_argument('email')
user_post_parser.add_argument('name')


class UserResource(Resource):
    @authenticate
    def get(self):
        return {"id": g.user.id,
                "name": g.user.name,
                "email": g.user.email}

    def post(self):
        args = user_post_parser.parse_args()
        u = User(email=args["email"], name=args["name"])
        db_session.add(u)
        db_session.commit()
        return "success"


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
            return "success"
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
            db_session.add(s)
            db_session.commit()
            return {"session_key": session_key}
        else:
            abort(500)


group_post_parser = reqparse.RequestParser()
group_post_parser.add_argument('name')


class GroupResource(Resource):
    def get(self):
        """
        Get list of groups
        """
        groups = Group.query.all()
        return groups

    def post(self):
        """
        Create new group
        """
        args = group_post_parser.parse_args()
        g = Group(name=args["name"], owner=g.id)
        db_session.add(g)
        db_session.commit()
        return "success"


class UserGroupResource(Resource):
    def post(self, group_id):
        """
        Join group
        """
        group = Group.query.filter_by(id=group_id).one()
        if not group:
            abort(500, message="No group with this ID")
        else:
            group.member.append(g.user)
            db_session.add(group)
            db_session.commit()
            return {"status": "success"}

    def delete(self, group_id):
        """
        Leave group
        """
        group = Group.query.filter_by(id=group_id).one()
        if not group:
            abort(500, message="No group with this ID")

        if g.user not in group.member:
            abort(500, message="Not a group member")

        group.member.remove(g.user)
        db_session.add(group)
        db_session.commit()
        return "success"


api.add_resource(UserResource, '/user')
api.add_resource(LoginResource, '/login/<string:email>')
api.add_resource(GroupResource, '/group')
api.add_resource(UserGroupResource, '/group/<int:group_id>')
api.add_resource(SessionResource, '/session/<string:login_token>')
