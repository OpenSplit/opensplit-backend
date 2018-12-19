#! /usr/bin/env python3
from flask_restful import Resource, reqparse, abort
from opensplit import api, db, app, models
from flask import g
from opensplit.helper import generate_random_string, send_mail, authenticate

user_post_parser = reqparse.RequestParser()
user_post_parser.add_argument('email', type=str, required=True)
user_post_parser.add_argument('name', type=str, required=True)


class UserResource(Resource):

    @authenticate
    def get(self):
        return g.user.jsonify()

    def post(self):
        args = user_post_parser.parse_args()
        email = args["email"]
        username = args["name"]
        if models.User.query.filter_by(email=email).first():
            return {"message": "email address exists"}, 409
        if models.User.query.filter_by(name=username).first():
            return {"message": "username exists"}, 409
        u = models.User(email=email, name=username)
        db.session.add(u)
        db.session.commit()
        return {"message": "success"}, 201


class SpecialUserResource(Resource):
    method_decorators = [authenticate]

    def get(self, user_id):
        user = models.User.query.get(user_id)
        if user:
            return {"id": user.id,
                    "name": user.name,
                    "groups": [grp.jsonify() for grp in user.groups],
                    "email": user.email}
        else:
            return {"message": "No user with this ID"}, 404

    def put(self, user_id):
        # TODO: Update user
        return "ok", 200

    def delete(self, user_id):
        # TODO: Delete user
        return "ok", 200


login_parser = reqparse.RequestParser()
login_parser.add_argument('userid')


class LoginResource(Resource):
    def get(self, email):
        """
        Generate a new login token
        """
        user = models.User.query.filter_by(email=email).first()
        if user:
            token = user.generate_login_token().decode()
            if app.config["EMAIL_ENABLED"]:
                login_url = "{}/login/{}".format(app.config['BASE_URL'], token)
                body_tmpl = "Hi {},\n your login token for OpenSplit is: {}\n"
                body = body_tmpl.format(user.name, login_url)

                send_mail(user.email, "New login token", body)
            else:
                print("Login-Token for {}:\n{}".format(user.name, token))
            return {"message": "success"}
        else:
            abort(500)


class SessionResource(Resource):
    def get(self, login_token):
        """
        Generate a new session
        """
        user = models.User.verify_login_token(login_token)
        if user:
            session_key = generate_random_string(length=50)
            s = models.Session(user=user, session_key=session_key)
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
        queryset = models.Group.query.all()
        return [grp.jsonify() for grp in queryset if g.user in grp.member]

    def post(self):
        args = group_post_parser.parse_args()
        group = models.Group(name=args["name"], owner=g.user.id)
        group.member.append(g.user)
        db.session.add(group)
        db.session.commit()
        return {"message": "success"}


class GroupDetailResource(Resource):
    method_decorators = [authenticate]

    def get(self, group_id):
        group = models.Group.query.filter_by(id=group_id).first()
        if not group:
            return {"message": "No group with this ID"}, 404
        else:
            if g.user not in group.member:
                return {"message": "Not a member of this group"}, 403
            return group.jsonify()


class GroupUsersResource(Resource):
    method_decorators = [authenticate]

    def get(self, group_id):
        group = models.Group.query.filter_by(id=group_id).first()
        if not group:
            return {"message": "No group with this ID"}, 404
        else:
            if g.user not in group.member:
                return {"message": "Not a member of this group"}, 403
            return [u.jsonify() for u in group.member]


class GroupTokenResource(Resource):
    method_decorators = [authenticate]

    def get(self, group_id):
        group = models.Group.query.filter_by(id=group_id).first()
        if not group:
            return {"message": "No group with this ID"}, 404
        else:
            if g.user not in group.member:
                return {"message": "Not a member of this group"}, 403
            return group.token


class GroupJoinResource(Resource):
    method_decorators = [authenticate]

    def get(self, token):
        group = models.Group.query.filter_by(token=token).first()
        if not group:
            return {"message": "No group with this token"}, 404
        else:
            return {"name": group.name,
                    "is_member": g.user in group.member}

    def post(self, token):
        group = models.Group.query.filter_by(token=token).first()
        if not group:
            return {"message": "No group with this token"}, 404
        else:
            group.member.append(g.user)
            db.session.add(group)
            db.session.commit()
            return "Group joined successfully"


class GroupLeaveResource(Resource):
    method_decorators = [authenticate]

    def post(self, group_id, token):
        group = models.Group.query.filter_by(id=group_id).first()
        if not group or g.user not in group.member:
            return {"message": "No group with this ID or not a member"}, 404
        else:
            group.member.remove(g.user)
            db.session.add(group)
            db.session.commit()
            return "Group left successfully"


expense_post_parser = reqparse.RequestParser()
expense_post_parser.add_argument('description', required=True)
expense_post_parser.add_argument('amount', required=True)
expense_post_parser.add_argument('paid_by', required=True)
expense_post_parser.add_argument(
    'split_amongst', action='append', required=True)


class TransactionResource(Resource):
    method_decorators = [authenticate]

    def get(self, group_id, page=0):
        group = models.Group.query.get(group_id)
        pagesize = 10
        if group:
            expenses = [expense.jsonify()
                        for expense in group.expenses if not expense.is_payment]
            i = page*pagesize
            return sorted(expenses, key=lambda k: k["date"], reverse=True)[i: i+pagesize]
        else:
            return {"message": "groupid doesn't exists"}, 404

    def post(self, group_id):
        group = models.Group.query.get(group_id)
        if group:
            args = expense_post_parser.parse_args()
            e = models.Expense(description=args["description"],
                               amount=float(args["amount"])*100,
                               group_id=group_id,
                               paid_by=args["paid_by"])
            for user_id in args["split_amongst"]:
                e.split_amongst.append(models.User.query.get(user_id))
            db.session.add(e)
            db.session.commit()
        else:
            return {"message": "groupid doesn't exists"}, 404


payment_post_parser = reqparse.RequestParser()
payment_post_parser.add_argument('amount', required=True)
payment_post_parser.add_argument('sender', required=True)
payment_post_parser.add_argument('receiver', required=True)


class PaymentResource(Resource):
    method_decorators = [authenticate]

    def get(self, group_id):
        group = models.Group.query.get(group_id)
        return [expense.jsonify() for expense in group.expenses if expense.is_payment]

    def post(self, group_id):
        args = payment_post_parser.parse_args()
        group = models.Group.query.get(group_id)
        receiver = models.User.query.get(args["receiver"])
        sender = models.User.query.get(args["sender"])

        if not (group or receiver or sender):
            return {"message": "Something with your data is wrong"}, 400

        e = models.Expense(description="Payment",
                           amount=float(args["amount"])*100,
                           group_id=group.id,
                           paid_by=sender.id,
                           is_payment=True)
        e.split_amongst.append(receiver)
        db.session.add(e)
        db.session.commit()
        return {"message": "success"}


class CheckResource(Resource):
    method_decorators = [authenticate]

    def get(self):
        return "ok", 200


api.add_resource(UserResource, '/users')
api.add_resource(SpecialUserResource, '/users/<int:user_id>')

api.add_resource(GroupResource, '/groups')
api.add_resource(GroupDetailResource, '/groups/<int:group_id>')
api.add_resource(GroupUsersResource, '/groups/<int:group_id>/users')
api.add_resource(GroupTokenResource, '/groups/<int:group_id>/generateToken')
api.add_resource(GroupLeaveResource, '/groups/<int:group_id>/leave')
api.add_resource(GroupJoinResource, '/groups/join/<string:token>')

api.add_resource(SessionResource, '/session/<string:login_token>')
api.add_resource(LoginResource, '/login/<string:email>')

api.add_resource(TransactionResource,
                 '/groups/<int:group_id>/transactions',
                 '/groups/<int:group_id>/transactions/<int:page>')

api.add_resource(PaymentResource, '/groups/<int:group_id>/payments')

api.add_resource(CheckResource, '/checktoken')
