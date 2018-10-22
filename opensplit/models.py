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

expense_assoc = Table('expense_assoc', db.Model.metadata,
                      Column('user_id', Integer, ForeignKey('user.id')),
                      Column('share', Numeric(10, 2)),
                      Column('expense_id', Integer, ForeignKey('expense.id'))
                      )


class User(db.Model):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False)
    name = Column(String(30), unique=True, nullable=False)
    sessions = relationship('Session', backref='user', lazy=True)
    expenses = relationship(
        "Expense",
        secondary=expense_assoc,
        back_populates="split_amongst")
    groups = relationship(
        "Group",
        secondary=group_assoc,
        back_populates="member")

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
    expenses = relationship('Expense', backref='group', lazy=True)
    member = relationship(
        "User",
        secondary=group_assoc,
        back_populates="groups")

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

        debts = helper.calculate_debts(self.id)
        for entry in group_data["member"]:
            try:
                entry["debts"] = debts[entry["name"]]
            except KeyError:
                entry["debts"] = {"total": 0, "owes": []}

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
    split_amongst = relationship(
        "User",
        secondary=expense_assoc,
        back_populates="expenses")

    def jsonify(self):
        return {"id": self.id,
                "description": self.description,
                "amount": float(self.amount/100),
                "date": str(self.date),
                "group_id": self.group_id,
                "paid_by": User.query.get(self.paid_by).jsonify(),
                "is_payment": self.is_payment,
                "split_amongst": [u.jsonify() for u in self.split_amongst]}


class History(db.Model):
    __tablename__ = 'history'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    event_type = Column(String(60), nullable=False)
    evend_id = Column(Integer, nullable=False)

    def jsonify(self):
        return {"id": self.id,
                "date": str(self.date),
                "event_type": self.event_type,
                "event_id": self.event_id}