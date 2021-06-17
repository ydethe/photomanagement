# Person.py
import io
import os
from enum import Enum, unique

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
from tqdm import tqdm
from mongoengine import signals
from PIL import Image, ImageDraw
from pkg_resources import require

from . import logger, db, am
from .AirtableManager import AirtableManager
from .Face import Face


class Person(db.Document):
    airtable_id = StringField(unique=True, required=True)
    faces = ListField(ReferenceField(Face))

    def getAirtableInformation(self):
        rec = am.get_rec_by_id("pers_table", self.airtable_id)
        return rec["fields"]

    def saveFaces(self):
        os.makedirs("persons/%s_%s" % (self.nom, self.id), exist_ok=True)
        for k, face in enumerate(self.faces):
            image = face.photo.photo.read()
            print(face.photo.id)
            img = Image.open(io.BytesIO(image))

            # Creating a miniature of the person's face
            mini = img.resize(
                size=(face.right - face.left, face.lower - face.upper),
                box=(face.left, face.upper, face.right, face.lower),
            )
            _, fn = os.path.split(face.photo.photo.filename)
            bn, _ = os.path.splitext(fn)
            bn = bn.replace(" ", "_")
            mini.save("persons/%s_%s/%s_face%i.jpg" % (self.nom, self.id, bn, k))

    def showFaces(self):
        for k, face in enumerate(self.faces):
            image = face.photo.photo.read()
            img = Image.open(io.BytesIO(image))

            # Drawing a red rectangle on the photo to locate the person
            img_with_red_box_draw = ImageDraw.Draw(img)
            img_with_red_box_draw.rectangle(
                [(face.left, face.upper), (face.right, face.lower)],
                outline="red",
                width=3,
            )
            img.show()
