import pickle
import io
import os
from enum import unique
from mongoengine import (
    connect,
    Document,
    IntField,
    StringField,
    ListField,
    ReferenceField,
    BooleanField,
    ImageField,
    DateTimeField,
    BinaryField,
)
import mongoshapes as ms
from PIL import Image, ImageDraw
import face_recognition
import numpy as np


class Face(Document):
    blob = BinaryField()
    xleft = IntField()
    xright = IntField()
    ydown = IntField()
    yup = IntField()
    photo = ReferenceField("Photo")
    person = ReferenceField("Person")
    manually_tagged = BooleanField(default=False)

    @classmethod
    def exportAll(cls, dst_dir="faces"):
        os.makedirs(dst_dir, exist_ok=True)
        for face in cls.objects():
            image = face.photo.photo.read()
            img_with_red_box = Image.open(io.BytesIO(image))

            # Creating a miniature of the person's face
            mini = img_with_red_box.resize(
                size=(face.xright - face.xleft, face.ydown - face.yup),
                box=(face.xleft, face.yup, face.xright, face.ydown),
            )
            _, fn = os.path.split(face.photo.photo.filename)
            bn, _ = os.path.splitext(fn)
            bn = bn.replace(" ", "_")
            mini.save("%s/%s.jpg" % (dst_dir, face.id))

    def affectToPersonAndSaveAll(self, person):
        person.faces.append(self)
        person.save()

        if not self.person is None:
            self.person.faces.remove(self)
            self.person.save()

        self.person = person
        self.manually_tagged = True
        self.save()


class Person(Document):
    nom = StringField()
    faces = ListField(ReferenceField(Face))

    def saveFaces(self):
        os.makedirs("persons/%s_%s" % (self.nom, self.id), exist_ok=True)
        for k, face in enumerate(self.faces):
            image = face.photo.photo.read()
            print(face.photo.id)
            img_with_red_box = Image.open(io.BytesIO(image))

            # Creating a miniature of the person's face
            mini = img_with_red_box.resize(
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
            img_with_red_box = Image.open(io.BytesIO(image))

            # Creating a miniature of the person's face
            mini = img_with_red_box.resize(
                size=(face.xright - face.xleft, face.ydown - face.yup),
                box=(face.xleft, face.yup, face.xright, face.ydown),
            )
            mini.save("persons/%s_%i.jpg" % (self.id, k))

            # Drawing a red rectangle on the photo to locate the person
            img_with_red_box_draw = ImageDraw.Draw(img_with_red_box)
            img_with_red_box_draw.rectangle(
                [(face.xleft, face.yup), (face.xright, face.ydown)],
                outline="red",
                width=3,
            )
            img_with_red_box.show()


class Photo(Document):
    photo = ImageField()
    hash = StringField(unique=True)
    place_taken = ms.PointField()
    miniature = ImageField(thumbnail_size=(200, 200))
    date_taken = DateTimeField(required=True)
    faces = ListField(ReferenceField(Face))
    album = ReferenceField("Album")

    @classmethod
    def showPhoto(cls, photo_id):
        photo = cls.objects(id=photo_id).first()
        image = photo.photo.read()
        img = Image.open(io.BytesIO(image))
        img.show()

    def showFaces(self):
        image = self.photo.read()

        img = Image.open(io.BytesIO(image))
        # img = Image.fromarray(image, "RGB")
        img_with_red_box = img.copy()
        img_with_red_box_draw = ImageDraw.Draw(img_with_red_box)

        for face in self.faces:
            img_with_red_box_draw.rectangle(
                [(face.xleft, face.yup), (face.xright, face.ydown)],
                outline="red",
                width=3,
            )

        img_with_red_box.show()


class Album(Document):
    titre = StringField()
    photos = ListField(ReferenceField(Photo))


# b = np.zeros(128, dtype=np.float64).tobytes()
# ross = Individu(airtable_id="rec7kGIwPvyF88c9B", blobs=[b])

# ross.save()

# for u in Individu.objects:
#     print(u.airtable_id)
