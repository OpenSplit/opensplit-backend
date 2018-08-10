#! /usr/bin/env python3
import os
import opensplit
import unittest
import tempfile

TEST_USER1 = {"EMAIL_ADDR": "lol@nope.com", "NAME": "John Doe"}
TEST_USER2 = {"EMAIL_ADDR": "yes@nope.com", "NAME": "Mark Ham"}
GROUP_NAME = "Testgroup"
TEST_EXPENSE1 = {"DESCRIPTION": "Testexpense", "AMOUNT": 13.37, "PAID_BY": 1, "SPLIT_AMONGST": [1]}

class OpenSplitTestCase(unittest.TestCase):

    def setUp(self):
        self.db_filehandle, self.db_filename = tempfile.mkstemp()
        opensplit.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(
            self.db_filename)
        opensplit.app.testing = True
        self.app = opensplit.app.test_client()
        with opensplit.app.app_context():
            opensplit.db.create_all()

    def tearDown(self):
        os.close(self.db_filehandle)

    def create_user(self, user):
        return self.app.post('/users', data=dict(
            email=user["EMAIL_ADDR"],
            name=user["NAME"]))

    def test_create_user(self):
        r = self.create_user(TEST_USER1)
        self.assertEqual(r.status, "201 CREATED")

    def test_user_login(self):
        self.create_user(TEST_USER1)

        rv = self.app.get('/login/{}'.format(TEST_USER1["EMAIL_ADDR"]))
        self.assertEqual(rv.status, "200 OK")

        # Generate our own login token because we won't receive emails
        user = opensplit.db.session.query(opensplit.models.User).first()
        login_token = user.generate_login_token()

        rv = self.app.get('/session/{}'.format(login_token.decode()))
        self.assertEqual(rv.status, "200 OK")
        self.assertIsNotNone(rv.json.get("session_key"))

    def login_user(self, user):
        self.create_user(user)

        # Generate our own login token because we won't receive emails
        user = opensplit.db.session.query(opensplit.models.User).first()
        login_token = user.generate_login_token()

        rv = self.app.get('/session/{}'.format(login_token.decode()))
        return rv.json.get("session_key")

    def create_group(self, session_key):
        self.app.post('/groups',
                      data={"name": GROUP_NAME},
                      headers={"Authorization": session_key})
        return opensplit.db.session.query(opensplit.models.Group).first().id

    def test_session_key(self):
        session_key = self.login_user(TEST_USER1)

        r = self.app.get('/users',
                         headers={"Authorization": session_key})

        self.assertEqual(r.status, "200 OK")
        self.assertEqual(r.json.get("name"), TEST_USER1["NAME"])
        self.assertEqual(r.json.get("email"), TEST_USER1["EMAIL_ADDR"])

    def create_expense(self, group_id, session_key, expense):
        return self.app.post('/groups/{}/transactions'.format(group_id),
                             data={"description": expense["DESCRIPTION"],
                                   "amount": expense["AMOUNT"],
                                   "group_id": group_id,
                                   "paid_by": expense["PAID_BY"],
                                   "split_amongst": expense["SPLIT_AMONGST"]},
                             headers={"Authorization": session_key})

    def test_add_and_get_expanse(self):
        session_key = self.login_user(TEST_USER1)
        group_id = self.create_group(session_key)
        r = self.create_expense(group_id, session_key, TEST_EXPENSE1)

        self.assertEqual(r.status, "200 OK")

        r = self.app.get('/groups/{}/transactions'.format(group_id),
                         headers={"Authorization": session_key})
        data = r.json
        testexpense = data[0]
        print(testexpense)
        self.assertEqual(len(data), 1)
        self.assertEqual(testexpense["amount"], TEST_EXPENSE1["AMOUNT"])
        self.assertEqual(testexpense["description"], TEST_EXPENSE1["DESCRIPTION"])
        self.assertEqual(testexpense["group_id"], group_id)
        self.assertEqual(len(testexpense["split_amongst"]), 1)


if __name__ == '__main__':
    unittest.main()
