#! /usr/bin/env python3
from functools import wraps
import random
from flask_restful import abort, request
from opensplit.models import Session, User
from flask import g


def authenticate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        session_key = request.headers.get("Authorization", None)
        if session_key:
            print("Got auth header")
            session = Session.query.filter_by(session_key=session_key).one()
            if session:
                print("Found valid session for this key")
                g.user = User.query.filter_by(id=session.user_id).one()
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
