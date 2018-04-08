#! /usr/bin/env python3
from opensplit.models import Group, User, Expense
from opensplit import db

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


e1 = Expense(description="Nudeln", amount="10.00", group_id=g.id, paid_by=u1.id)
e1.split_amongst.append(u2)
e1.split_amongst.append(u3)

e2 = Expense(description="Pizza", amount="20.00", group_id=g.id, paid_by=u2.id)
e2.split_amongst.append(u1)
e2.split_amongst.append(u3)

e3 = Expense(description="Torte", amount="12.23", group_id=g.id, paid_by=u3.id)
e3.split_amongst.append(u1)
e3.split_amongst.append(u3)

e4 = Expense(description="LOLWUUT", amount="42.23", group_id=g.id, paid_by=u1.id)
e4.split_amongst.append(u1)
e4.split_amongst.append(u2)
e4.split_amongst.append(u3)

db.session.add(e1)
db.session.add(e2)
db.session.add(e3)
db.session.add(e4)
db.session.commit()
