#! /usr/bin/env python3
from opensplit import app, db, helper
from sqlalchemy import Table, Column, Integer, String, Boolean, ForeignKey, Numeric, DateTime
from sqlalchemy.orm import relationship
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired, BadSignature
from datetime import datetime

group_assoc = Table('group_assoc', db.Model.metadata,
                    Column('user_id', Integer, ForeignKey('user.id')),
                    Column('group_id', Integer, ForeignKey('group.id'))
                    )

class Share(db.Model):
    __tablename__ = 'expense_assoc'
    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    expense_id = Column(Integer, ForeignKey('expense.id'), primary_key=True)
    amount = Column(Integer)
    expense = relationship("Expense")
    user = relationship("User")


class User(db.Model):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False)
    name = Column(String(30), unique=True, nullable=False)
    sessions = relationship('Session', backref='user', lazy=True)
    shares = relationship("Share")
    groups = relationship(
        "Group",
        secondary=group_assoc)

    def generate_login_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    def jsonify(self):
        return {"id": self.id,
                "name": self.name,
                "email": self.email}

    @staticmethod
    def verify_login_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            # valid token, but expired
            return None
        except BadSignature:
            # invalid token
            return None
        user = User.query.get(data['id'])
        return user


class Session(db.Model):
    __tablename__ = 'session'
    id = Column(Integer, primary_key=True)
    session_key = Column(String(120), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)

class Group(db.Model):
    __tablename__ = 'group'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    token = Column(String(40), nullable=False)
    owner = Column(Integer, ForeignKey('user.id'), nullable=False)
    expenses = relationship('Expense', lazy=True)
    member = relationship(
        "User",
        secondary=group_assoc
        )

    def __init__(self, name, owner):
        self.name = name
        self.owner = owner
        self.token = helper.generate_random_string(url=True, length=30)

    def jsonify(self):
        group_data = {"id": self.id,
                      "name": self.name,
                      "token": helper.generate_invite_link(self.token),
                      "owner": self.owner,
                      "member": [u.jsonify() for u in self.member]}

        debts = helper.simplify_debts(self.id)
        for entry in group_data["member"]:
            entry["debts"] = helper.format_obligations(entry['id'], debts)

        return group_data


class Expense(db.Model):
    __tablename__ = 'expense'
    id = Column(Integer, primary_key=True)
    description = Column(String(120), nullable=False)
    amount = Column(Integer, nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_payment = Column(Boolean, nullable=False, default=False)
    group_id = Column(Integer, ForeignKey('group.id'), nullable=False)
    paid_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    participants = relationship('Share')

    def jsonify(self):
        return {"id": self.id,
                "description": self.description,
                "amount": float(self.amount/100),
                "date": str(self.date),
                "group_id": self.group_id,
                "paid_by": User.query.get(self.paid_by).jsonify(),
                "is_payment": self.is_payment,
                "split_amongst": [u.jsonify() for u in self.split_amongst]}


class Event(db.Model):
    __tablename__ = 'history'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    group_id = Column(Integer, ForeignKey('group.id'), nullable=False)
    event_type = Column(String(60), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    expense_id = Column(Integer, ForeignKey('expense.id'))

    def __init__(self, group_id, event_type, user_id=None, expense_id=None):
        if helper.is_valid_event_type(event_type):
            self.group_id = group_id
            self.event_type = event_type
            self.user_id = user_id
            self.expense_id = expense_id
        else:
            raise ValueError("Invalid event type")

    def jsonify(self):
        data = {"id": self.id,
                "date": str(self.date),
                "event_type": self.event_type}

        if self.user_id:
            data["user"] = User.query.get(self.user_id).jsonify()
        elif self.expense_id:
            data["expense"] = Expense.query.get(self.expense_id).jsonify()

        return data
