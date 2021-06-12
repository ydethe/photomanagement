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

from . import logger, db
from .AirtableManager import AirtableManager


# db.createUser(
#   {
#     user: "ydethe",
#     pwd: passwordPrompt(),  // or cleartext password
#     roles: [
#        { role: "readWrite", db: "photo_mgt" }
#     ]
#   }
# )


def handler(event):
    """Signal decorator to allow use of callback functions as class decorators."""

    def decorator(fn):
        def apply(cls):
            event.connect(fn, sender=cls)
            return cls

        fn.apply = apply
        return fn

    return decorator


@handler(signals.post_delete)
def face_suppressed(sender, document):
    logger.debug("Suppress face %s from photo %s" % (document.id, document.photo.id))
    document.photo.faces.remove(document)
    document.photo.save()

    if not document.person is None:
        logger.debug(
            "Suppress face %s from person %s" % (document.id, document.person.id)
        )
        document.person.faces.remove(document)
        document.person.save()


@handler(signals.pre_delete)
def photo_suppressed(sender, document):
    logger.debug("Suppress photo %s (%s)" % (document.id, document.original_path))
    for face in document.faces:
        logger.debug("   Suppress face %s" % face.id)
        face.delete()

    if not document.place_taken is None:
        document.place_taken.photos.remove(document)

    if not document.album is None:
        document.album.photos.remove(document)


# https://stackoverflow.com/questions/62986950/deleting-a-reference-in-a-mongoengine-listfield
@face_suppressed.apply
class Face(db.Document):
    hash = StringField(unique=True, required=True)
    blob = ListField(FloatField())
    xleft = IntField()
    xright = IntField()
    ydown = IntField()
    yup = IntField()
    photo = ReferenceField("Photo", required=True)
    person = ReferenceField("Person")
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
        mini = img.resize(
            size=(self.xright - self.xleft, self.ydown - self.yup),
            box=(self.xleft, self.yup, self.xright, self.ydown),
        )
        return mini

    def showPhoto(self):
        image = self.photo.photo.read()
        img = Image.open(io.BytesIO(image))

        # Drawing a red rectangle on the photo to locate the person
        img_with_red_box_draw = ImageDraw.Draw(img)
        img_with_red_box_draw.rectangle(
            [(self.xleft, self.yup), (self.xright, self.ydown)], outline="red", width=3,
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


class Person(db.Document):
    airtable_id = StringField(unique=True, required=True)
    faces = ListField(ReferenceField(Face))

    def getAirtableInformation(self):
        am = AirtableManager(fic_cfg="etc/pmg.conf")
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
                size=(face.xright - face.xleft, face.ydown - face.yup),
                box=(face.xleft, face.yup, face.xright, face.ydown),
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
                [(face.xleft, face.yup), (face.xright, face.ydown)],
                outline="red",
                width=3,
            )
            img.show()


class Address(db.Document):
    ville = StringField()
    pays = StringField()
    rue = StringField()
    numero = IntField()
    code_postal = StringField()
    latitude = FloatField()
    longitude = FloatField()
    altitude = FloatField()
    photos = ListField(ReferenceField("Photo"))
    w3w = StringField(unique=True)


@photo_suppressed.apply
class Photo(db.Document):
    photo = ImageField()
    original_path = StringField(required=True)
    hash = StringField(unique=True, required=True)
    place_taken = ReferenceField("Address")
    miniature = ImageField(thumbnail_size=(200, 200))
    date_taken = DateTimeField(required=True)
    faces = ListField(ReferenceField(Face))
    album = ReferenceField("Album")
    inferred_date = BooleanField()
    original_exif = DictField()

    @classmethod
    def showPhoto(cls, photo_id, show_faces=False):
        photo = cls.objects(id=photo_id).first()
        image = photo.photo.read()
        img = Image.open(io.BytesIO(image))

        if show_faces:
            # Drawing a red rectangle on the photo to locate the person
            img_with_red_box_draw = ImageDraw.Draw(img)
            for face in photo.faces:
                img_with_red_box_draw.rectangle(
                    [(face.xleft, face.yup), (face.xright, face.ydown)],
                    outline="red",
                    width=3,
                )

        img.show()

    def show(self, show_faces=True):
        image = self.photo.read()
        img = Image.open(io.BytesIO(image))

        if show_faces:
            img_with_red_box_draw = ImageDraw.Draw(img)

            for face in self.faces:
                img_with_red_box_draw.rectangle(
                    [(face.xleft, face.yup), (face.xright, face.ydown)],
                    outline="red",
                    width=3,
                )

        img.show()


class Album(db.Document):
    titre = StringField()
    photos = ListField(ReferenceField(Photo))
