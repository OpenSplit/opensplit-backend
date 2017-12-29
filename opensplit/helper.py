#! /usr/bin/env python3
from functools import wraps
import random
from flask_restful import abort, request
from opensplit.models import Session, User
from flask import g
from random import shuffle


def authenticate(func):
    """
    Wrapper which checks for valid "Authorization" Headers in a request
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        session_key = request.headers.get("Authorization", None)
        if session_key:
            session = Session.query.filter_by(session_key=session_key).first()
            if session:
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
    """
    Generate a long and secure string
    - Code stolen from Django Project -
    """
    allowed_chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    length = 50
    return ''.join(random.choice(allowed_chars) for i in range(length))


def split_amongst(amount, user):
    """
    Take a value of "amount" and fairly split it amongst the given
    list of "user"
    """
    foo = amount // len(user)
    rest = amount - (foo * len(user))

    debts = []
    # Jeder bezahlt erstmal das gleiche
    for _ in range(len(user)):
        debts.append(foo)

    # Den Rest fair verteilen
    for i in range(rest):
        debts[i] = debts[i] + 1

    # Shuffeln für mehr fairness
    shuffle(debts)

    # Sanity check
    if sum(debts) != amount:
        print("FUCK")
        print(amount)
        print(debts)

    return list(zip(user, debts))
