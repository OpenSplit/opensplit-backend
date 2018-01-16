import os
basedir = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = "yeKawoowied9pi8eod5a"

# Database
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'var/opensplit.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
