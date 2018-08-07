#! /usr/bin/env python3
import os
import opensplit
import unittest
import tempfile

EMAIL_ADDR = "lol@nope.com"
USER_NAME = "John Doe"
GROUP_NAME = "Testgroup"
EXPENSE_DESCRIPTION = "Testexpense"
EXPENSE_AMOUNT = 13.37


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

    def create_user(self):
        return self.app.post('/users', data=dict(
            email=EMAIL_ADDR,
            name=USER_NAME))

    def test_create_user(self):
        r = self.create_user()
        self.assertEqual(r.status, "201 CREATED")

    def test_user_login(self):
        self.create_user()

        rv = self.app.get('/login/{}'.format(EMAIL_ADDR))
        self.assertEqual(rv.status, "200 OK")

        # Generate our own login token because we won't receive emails
        user = opensplit.db.session.query(opensplit.models.User).first()
        login_token = user.generate_login_token()

        rv = self.app.get('/session/{}'.format(login_token.decode()))
        self.assertEqual(rv.status, "200 OK")
        self.assertIsNotNone(rv.json.get("session_key"))

    def login_user(self):
        self.create_user()

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
        session_key = self.login_user()

        r = self.app.get('/users',
                         headers={"Authorization": session_key})

        self.assertEqual(r.status, "200 OK")
        self.assertEqual(r.json.get("name"), USER_NAME)
        self.assertEqual(r.json.get("email"), EMAIL_ADDR)

    def test_add_and_get_expanse(self):
        session_key = self.login_user()
        group_id = self.create_group(session_key)

        r = self.app.post('/groups/{}/transactions'.format(group_id),
                          data={"description": EXPENSE_DESCRIPTION,
                                "amount": EXPENSE_AMOUNT,
                                "group_id": group_id,
                                "paid_by": 1,
                                "split_amongst": [1]},
                          headers={"Authorization": session_key})

        self.assertEqual(r.status, "200 OK")

        r = self.app.get('/groups/{}/transactions'.format(group_id),
                         headers={"Authorization": session_key})
        data = r.json
        testexpense = data[0]
        self.assertEqual(len(data), 1)
        self.assertEqual(testexpense["amount"], EXPENSE_AMOUNT)


if __name__ == '__main__':
    unittest.main()
