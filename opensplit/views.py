#! /usr/bin/env python3
from flask_restful import Resource, reqparse, abort
from opensplit import api, db
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
                "groups": [grp.name for grp in g.user.groups],
                "email": g.user.email}

    def post(self):
        args = user_post_parser.parse_args()
        u = User(email=args["email"], name=args["name"])
        db.session.add(u)
        db.session.commit()
        return {"message":"success"}


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
            return {"message":"success"}
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


group_post_parser = reqparse.RequestParser()
group_post_parser.add_argument('name')


class GroupResource(Resource):
    method_decorators = [authenticate]
    def get(self):
        """
        Get list of groups
        """
        groups = Group.query.all()
        return [{"name": grp.name, "id": grp.id, "owner": grp.owner} for grp in groups]

    def post(self):
        """
        Create new group
        """
        args = group_post_parser.parse_args()
        group = Group(name=args["name"], owner=g.user.id)
        group.member.append(g.user)
        db.session.add(group)
        db.session.commit()
        return {"message":"success"}


class UserGroupResource(Resource):
    method_decorators = [authenticate]
    def post(self, group_id):
        """
        Join group
        """
        group = Group.query.filter_by(id=group_id).first()
        if not group:
            abort(500, message="No group with this ID")
        else:
            if g.user in group.member:
                abort(500, message="Allready member of this group")
            group.member.append(g.user)
            db.session.add(group)
            db.session.commit()
            return {"status": "success"}

    def delete(self, group_id):
        """
        Leave group
        """
        group = Group.query.filter_by(id=group_id).first()
        if not group:
            abort(500, message="No group with this ID")

        if g.user not in group.member:
            abort(500, message="Not a group member")

        group.member.remove(g.user)
        db.session.add(group)
        db.session.commit()
        return "success"


api.add_resource(UserResource, '/user')
api.add_resource(LoginResource, '/login/<string:email>')
api.add_resource(GroupResource, '/group')
api.add_resource(UserGroupResource, '/group/<int:group_id>')
api.add_resource(SessionResource, '/session/<string:login_token>')
