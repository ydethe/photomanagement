# User.py
import os

from mongoengine import StringField, EmailField, BooleanField

from . import logger, db, bcrypt


class User(db.Document):
    email = EmailField(required=True, unique=True)
    hashed_pwd = StringField(required=True)

    def isCorrectPassword(self, plaintext: str) -> bool:
        return bcrypt.check_password_hash(self.hashed_pwd, plaintext)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)
