#! /usr/bin/env python3
from functools import wraps
import random
from flask_restful import abort, request
from flask import g
from random import shuffle
from opensplit.models import Session, User, Group


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
        print("WARNING: The money was not distributed correctly!")
        print(amount)
        print(debts)

    return list(zip(user, debts))


def calculate_debts(group_id):
    group = Group.query.get(group_id)
    debts = {}

    # Generate debts between users
    for exp in group.expenses:
        payer = User.query.get(exp.paid_by)
        distribution = split_amongst(int(exp.amount*100), [u.name for u in exp.split_amongst])

        print("paid: {} -> shares: {}".format(payer.name,distribution))
        for user, amount in distribution:
            if user == payer.name:
                continue
            if not debts.get(user, None):
                debts[user] = {}

            debts[user][payer.name] = amount + debts[user].get(payer.name, 0)

    # Iterate over debts-dict again to "verrrechner hin und rückschulden" between 2 user
    for userA, userdebts in debts.items():
        for userB in userdebts.keys():
            try:
                diff = min(debts[userA][userB], debts[userB][userA])
                debts[userA][userB] -= diff
                debts[userB][userA] -= diff
            except KeyError:
                continue

    # Change format and remove empty lines
    debt_triples = []
    for userA, userdebts in debts.items():
        for userB, value in userdebts.items():
            if value > 0:
                debt_triples.append((userA, userB, value))

    return debt_triples
