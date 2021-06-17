# Album.py
from mongoengine import (
    Document,
    IntField,
    FloatField,
    StringField,
    ListField,
    ReferenceField,
    BooleanField,
    ImageField,
    DateTimeField,
    DictField,
    EmailField,
    EnumField,
    URLField,
)

from . import logger, db


class Album(db.Document):
    titre = StringField()
    photos = ListField(ReferenceField("Photo"))
