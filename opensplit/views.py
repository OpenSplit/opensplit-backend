#! /usr/bin/env python3
from flask_restful import Resource, reqparse, abort
from opensplit import api, db
from flask import g
from opensplit.models import User, Session, Group, Expense
from opensplit.helper import authenticate, generate_session_key
from sqlalchemy.exc import IntegrityError

user_post_parser = reqparse.RequestParser()
user_post_parser.add_argument('email')
user_post_parser.add_argument('name')


class UserResource(Resource):
    @authenticate
    def get(self):
        return {"id": g.user.id,
                "name": g.user.name,
                "groups": [{"name": grp.name,"id": grp.id} for grp in g.user.groups],
                "email": g.user.email}

    def post(self):
        args = user_post_parser.parse_args()
        u = user(email=args["email"], name=args["name"])
        db.session.add(u)
        db.session.commit()
        return {"message":"success"}

class SpecialUserResource(Resource):
    @authenticate
    def get(self, user_id):
        user = User.query.get(user_id)
        if user:
            return {"id": user.id,
                    "name": user.name,
                    "groups": [{"name": grp.name,"id": grp.id} for grp in user.groups],
                    "email": user.email}
        else:
            abort(500, message="No user with this ID")


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

    def get(self, group_id):
        """
        Get information about a specific group
        """
        group = Group.query.filter_by(id=group_id).first()
        if not group:
            abort(500, message="No group with this ID")
        else:
            if g.user not in group.member:
                abort(500, message="Not a member of this group")
            return {"name": group.name,
                    "id": group.id,
                    "member": [{"id":u.id, "name":u.name} for u in group.member],
                    "expenses": [e.id for e in group.expenses]}


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


expense_post_parser = reqparse.RequestParser()
expense_post_parser.add_argument('description')
expense_post_parser.add_argument('amount')
expense_post_parser.add_argument('group_id')
expense_post_parser.add_argument('paid_by')
expense_post_parser.add_argument('split_amongst', action='append')


class ExpenseResource(Resource):
    method_decorators = [authenticate]


    def post(self):
        """
        Add expenses
        """
        args = expense_post_parser.parse_args()
        e = Expense(description=args["description"], amount=args["amount"],
                    group_id=args["group_id"], paid_by=args["paid_by"])
        print(args)
        print(args["split_amongst"])
        for user_id in args["split_amongst"]:
            e.split_amongst.append(User.query.filter_by(id=user_id).first())
        db.session.add(e)
        db.session.commit()


api.add_resource(UserResource, '/user')
api.add_resource(SpecialUserResource, '/user/<int:user_id>')
api.add_resource(LoginResource, '/login/<string:email>')
api.add_resource(GroupResource, '/group')
api.add_resource(UserGroupResource, '/group/<int:group_id>')
api.add_resource(SessionResource, '/session/<string:login_token>')
api.add_resource(ExpenseResource, '/expense')
