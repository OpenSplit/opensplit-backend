#! /usr/bin/env python3
from functools import wraps
import random
from flask_restful import abort, request
from flask import g
from random import shuffle
from opensplit import models, app
from smtplib import SMTP_SSL, SMTP
from email.message import EmailMessage


def send_mail(receiver, subject, body):
    msg = EmailMessage()
    msg.set_content(body)

    msg['Subject'] = subject
    msg['From'] = app.config["SMTP_FROM"]
    msg['To'] = receiver

    hostname =  app.config["SMTP_HOST"]
    port =  app.config["SMTP_PORT"]

    if app.config["SMTP_SSL"]:
        s = SMTP_SSL(hostname, port)
    else:
        s = SMTP(hostname, port)

    s.login(app.config["SMTP_USER"], app.config["SMTP_PASS"])
    s.send_message(msg)
    s.quit()


def authenticate(func):
    """
    Wrapper which checks for valid "Authorization" Headers in a request
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        session_key = request.headers.get("Authorization", None)
        if session_key:
            session = models.Session.query.filter_by(session_key=session_key).first()
            if session:
                g.user = models.User.query.filter_by(id=session.user_id).one()
                return func(*args, **kwargs)
            else:
                print("can't find a valid session for this key")
                abort(401)
        else:
            print("No auth header")
            abort(401)
    return wrapper


def generate_random_string(url=False, length=50):
    """
    Generate a long and secure string
    - Code stolen from Django Project -
    """
    if url:
        allowed_chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    else:
        allowed_chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'

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
    group = models.Group.query.get(group_id)
    debts = {}

    # Generate debts between users
    for exp in group.expenses:
        payer = models.User.query.get(exp.paid_by)
        distribution = split_amongst(int(exp.amount*100), [u.name for u in exp.split_amongst])

        print("paid: {} -> shares: {}".format(payer.name, distribution))
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
    debts_clean = {m.name: {"owes": [], "total": 0} for m in group.member}

    for userA, userdebts in debts.items():
        for userB, value in userdebts.items():
            if value > 0:

                # Debts for userA, is credit for userB
                debts_clean[userA]["total"] -= value/100
                debts_clean[userB]["total"] += value/100

                debts_clean[userA]["owes"].append((userB, value/100))

    return debts_clean
