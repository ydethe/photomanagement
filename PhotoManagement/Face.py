# Face.py
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
from .utils.db import handler


@handler(signals.post_delete)
def face_suppressed(sender, document):
    if not document.photo is None:
        logger.debug(
            "Suppress face %s from photo %s" % (document.id, document.photo.id)
        )
        document.photo.faces.remove(document)
        document.photo.save()

    if not document.person is None:
        logger.debug(
            "Suppress face %s from person %s" % (document.id, document.person.id)
        )
        document.person.faces.remove(document)
        document.person.save()


# https://stackoverflow.com/questions/62986950/deleting-a-reference-in-a-mongoengine-listfield
@face_suppressed.apply
class Face(db.Document):
    hash = StringField(unique=True, required=True)
    embedding = ListField(FloatField())
    left = IntField()
    right = IntField()
    lower = IntField()
    upper = IntField()
    photo = ReferenceField("Photo", required=True)
    person = ReferenceField("Person")
    detection_score = FloatField()
    # landmarks = DictField()
    manually_tagged = BooleanField(default=False)

    @classmethod
    def exportAll(cls, dst_dir="faces"):
        os.makedirs(dst_dir, exist_ok=True)
        for face in tqdm(cls.objects()):
            # Creating a miniature of the person's face
            mini = face.getImage()
            _, fn = os.path.split(face.photo.photo.filename)
            bn, _ = os.path.splitext(fn)
            bn = bn.replace(" ", "_")
            mini.save("%s/%s.jpg" % (dst_dir, face.hash))

    @classmethod
    def showPhotoForFace(cls, **kwargs):
        face = cls.objects(**kwargs).first()
        face.showPhoto()

    def getImage(self) -> Image:
        image = self.photo.photo.read()
        img = Image.open(io.BytesIO(image))

        # Creating a miniature of the person's face
        face_img = img.crop((self.left, self.upper, self.right, self.lower))

        mini = img.resize(
            size=(self.right - self.left, self.lower - self.upper),
            box=(self.left, self.upper, self.right, self.lower),
        )
        return mini

    def showPhoto(self):
        image = self.photo.photo.read()
        img = Image.open(io.BytesIO(image))

        # Drawing a red rectangle on the photo to locate the person
        img_with_red_box_draw = ImageDraw.Draw(img)
        img_with_red_box_draw.rectangle(
            [(self.left, self.upper), (self.right, self.lower)], outline="red", width=3,
        )

        img.show()

    def affectToPersonAndSaveAll(self, person):
        person.faces.append(self)
        person.save()

        if not self.person is None:
            self.person.faces.remove(self)
            self.person.save()

        self.person = person
        self.manually_tagged = True
        self.save()
