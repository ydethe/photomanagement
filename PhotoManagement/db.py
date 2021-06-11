from collections import defaultdict
import io
import os
from enum import Enum

from mongoengine import (
    connect,
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
from PIL import Image, ImageDraw


class Face(Document):
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
        for face in cls.objects():
            image = face.photo.photo.read()
            img = Image.open(io.BytesIO(image))

            # Creating a miniature of the person's face
            mini = img.resize(
                size=(face.xright - face.xleft, face.ydown - face.yup),
                box=(face.xleft, face.yup, face.xright, face.ydown),
            )
            _, fn = os.path.split(face.photo.photo.filename)
            bn, _ = os.path.splitext(fn)
            bn = bn.replace(" ", "_")
            mini.save("%s/%s.jpg" % (dst_dir, face.id))

    def showPhoto(self):
        self.photo.photo.read()
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


class Organisation(Document):
    name = StringField()
    persons = ListField(ReferenceField("Person"))


class Title(Enum):
    NONE = ""
    FRERE = "Frère"
    PERE = "Père"
    SOEUR = "Soeur"


class Particle(Enum):
    NONE = ""
    DE = "de"
    DU = "du"
    D = "d'"
    DELA = "de la"
    LE = "le"


class Tag(Enum):
    AMI = "Ami"
    COLLEGUE = "Collègue"
    FAMILLE = "Famille"


class Person(Document):
    address = ReferenceField("Address")
    faces = ListField(ReferenceField(Face))
    linked_persons = ReferenceField("Person")
    mobile_perso = StringField()
    mobile_pro = StringField()
    notes = StringField()
    organisation = ReferenceField("Organisation")
    job_title = StringField()
    fix_pro = StringField()
    title = EnumField(Title, default=Title.NONE)
    firstname = StringField()
    particle = EnumField(Particle, default=Particle.NONE)
    familyname = StringField()
    email_perso = EmailField()
    email_pro = EmailField()
    date_birth = DateTimeField()
    linkedin = URLField()
    tag = EnumField(Tag, default=Tag.AMI)

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


class Address(Document):
    ville = StringField()
    pays = StringField()
    rue = StringField()
    numero = IntField()
    code_postal = StringField()
    latitude = FloatField()
    longitude = FloatField()
    altitude = FloatField()
    persons = ListField(ReferenceField("Person"))
    photos = ListField(ReferenceField("Photo"))
    w3w = StringField(unique=True)


class Photo(Document):
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


class Album(Document):
    titre = StringField()
    photos = ListField(ReferenceField(Photo))
