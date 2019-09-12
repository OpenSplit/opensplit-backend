#! /usr/bin/env python3
import random
from collections import defaultdict
from datetime import datetime
from email.message import EmailMessage
from flask import g
from flask_restful import abort, request
from functools import wraps
from random import shuffle
from smtplib import SMTP_SSL, SMTP
from uuid import uuid4 as random_uuid
from pprint import pprint

from opensplit import models, app

ALL_EVENTS = ["CREATED", "USER_JOINED", "USER_LEFT", "EXPENSE_CREATED",
              "EXPENSE_DELETED", "PAYMENT_CREATED", "PAYMENT_DELETED"]


def is_valid_event_type(event_type):
    return event_type in ALL_EVENTS


def send_mail(receiver, subject, body):
    msg = EmailMessage()
    msg.add_header(
        "Message-Id", "<{uuid}@{domain}>".format(
            uuid=random_uuid(),
            domain=app.config["SMTP_FROM"].split("@", 1)[1]
        )
    )
    msg.add_header("Date", datetime.now().strftime("%c"))
    msg.add_header("Subject", subject)
    msg.add_header("From", app.config["SMTP_FROM"])
    msg.add_header("To", receiver)
    msg.set_content(body)

    hostname = app.config["SMTP_HOST"]
    port = app.config["SMTP_PORT"]

    if app.config["SMTP_SSL"]:
        conn = SMTP_SSL(hostname, port)
    else:
        conn = SMTP(hostname, port)

    conn.login(app.config["SMTP_USER"], app.config["SMTP_PASS"])
    conn.send_message(msg)
    conn.quit()


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
                abort(401)
        else:
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


def split(amount, users):   
    """
    Takes an amount of money and splits it evenly between a number of users
    """
    share = amount // len(users)
    rest = amount - (len(users) * share)

    # rest is the amount of users that need to pay an extra cent
    #   0 <= rest < len(users)
    distribution = rest * [share + 1]
    
    # len(users) - rest is the amount of people that only pay the normal share
    distribution.extend((len(users) - rest) * [share])

    try:
        assert(sum(distribution) == amount)
    except AssertionError:
        print("WARNING: The money was not distributed correctly!")
        print(amount)
        print(distribution)

    return distribution


def assign_debts(amount, users):
    # distribute (possibly uneven) shares randomly among users to improve fairness
    distribution = split(amount, users)
    shuffle(distribution)
    return list(zip(users, distribution))


def simplify_debts(group_id):
    group = models.Group.query.get(group_id)

    # debtor owes creditor amount
    obligations = {}

    # traverse all expenses in a group
    for expense in group.expenses:
        # and accumulate debt shares towards creditors
        for share in expense.participants:
            # a creditor cannot be its own debtor
            if share.user.id == expense.paid_by:
                continue

            # share.debtor owes creditor share.amount
            if not obligations.get(share.user.id, None):
                # TODO: Replace with nifty defaultdict() shenanigans
                obligations[share.user.id] = {}
            obligations[share.user.id][expense.paid_by] = obligations[share.user.id].get(expense.paid_by, 0) + share.amount

    # simplify mutual debt
    for debtor, debts in obligations.items():
        for creditor, debt in debts.items():
            try:
                # the minimum amount both parties owe each other can be deducted
                mutual_debt = min(debt, obligations[creditor][debtor])
                obligations[debtor][creditor] -= mutual_debt
                obligations[creditor][debtor] -= mutual_debt
            except KeyError:
                # obligations can be unidirectional
                continue
                
    # TODO: simplify transitive relationships
    
    return obligations

def format_obligations(user, obligations):
    """
    Build the simplified list of debts and credits for a user
    """

    out = {}
    total = 0

    # user owes money to the creditors
    out['creditors'] = obligations[user]
    total -= sum(obligations[user].values())

    # user is owed money by the debtors
    out['debtors'] = {}
    for debtor, credit in obligations.items():
        for creditor, amount in credit.items():
            if creditor != user:
                continue
            out['debtors'][debtor] = amount
            total += amount

    out['total'] = total

    return out


def generate_invite_link(group_token):
    return "{}/invite/{}".format(app.config["BASE_URL"], group_token)
