#! /usr/bin/env python3
from opensplit.models import Group, User, Expense, Share
from opensplit.helper import assign_debts
from opensplit import db
from opensplit.helper import split, assign_debts

# Add users
u1 = User(name="Fleaz", email="mail@fleaz.org")
u2 = User(name="Evilet", email="mail@evilet.org")
u3 = User(name="Hexa", email="mail@hexa.org")

db.session.add(u1)
db.session.add(u2)
db.session.add(u3)
db.session.commit()

# Add group
g = Group(name="cccda", owner=u1.id)
g.member.append(u1)
g.member.append(u2)
g.member.append(u3)

db.session.add(g)
db.session.commit()


amount = 1000
users = [u2, u3]
e1 = Expense(description="Nudeln", amount=amount, group_id=g.id, paid_by=u1.id)
for user, amount in assign_debts(amount, users):
    s = Share(amount = amount)
    s.user = user
    e1.participants.append(s)

amount = 2000
users = [u1, u3]
e2 = Expense(description="Pizza", amount="2000", group_id=g.id, paid_by=u2.id)
for user, amount in assign_debts(amount, users):
    s = Share(amount = amount)
    s.user = user
    e2.participants.append(s)

amount = 1223
users = [u1, u3]
e3 = Expense(description="Torte", amount="1223", group_id=g.id, paid_by=u3.id)
for user, amount in assign_debts(amount, users):
    s = Share(amount = amount)
    s.user = user
    e3.participants.append(s)

amount = 4223
users = [u1, u2, u3]
e4 = Expense(description="LOLWUUT", amount="4223", group_id=g.id, paid_by=u1.id)
for user, amount in assign_debts(amount, users):
    s = Share(amount = amount)
    s.user = user
    e4.participants.append(s)

db.session.add(e1)
db.session.add(e2)
db.session.add(e3)
db.session.add(e4)
db.session.commit()

print("Done")
