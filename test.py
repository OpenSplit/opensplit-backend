#! /usr/bin/env python3
import os
import opensplit
import unittest
import tempfile

class OpenSplitTestCase(unittest.TestCase):

    def setUp(self):
        self.db_filehandle, self.db_filename = tempfile.mkstemp()
        opensplit.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(self.db_filename)
        opensplit.app.testing = True
        self.app = opensplit.app.test_client()
        with opensplit.app.app_context():
            opensplit.db.create_all()

    def tearDown(self):
        os.close(self.db_filehandle)

    def test_create_user(self):
        rv = self.app.post('/user', data=dict(
                email='lol@nope.com',
                name='John Doe'))

        assert rv.status == "200 OK"


if __name__ == '__main__':
    unittest.main()

