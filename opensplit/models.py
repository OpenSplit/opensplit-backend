#! /usr/bin/env python3
from opensplit import app
from sqlalchemy import Table, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired, BadSignature
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

association_table = Table('association', Base.metadata,
        Column('user_id', Integer, ForeignKey('user.id')),
        Column('group_id', Integer, ForeignKey('group.id'))
        )


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False)
    name = Column(String(30), unique=True, nullable=False)
    sessions = relationship('Session', backref='user', lazy=True)
    groups = relationship(
        "Group",
        secondary=association_table,
        back_populates="member")

    def generate_login_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

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


class Session(Base):
    __tablename__ = 'session'
    id = Column(Integer, primary_key=True)
    session_key = Column(String(120), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)


class Group(Base):
    __tablename__ = 'group'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True, nullable=False)
    owner = Column(Integer, ForeignKey('user.id'), nullable=False)
    member = relationship(
        "User",
        secondary=association_table,
        back_populates="groups")
