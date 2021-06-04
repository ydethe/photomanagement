import pickle
import io
from enum import unique
from mongoengine import (
    connect,
    Document,
    IntField,
    StringField,
    ListField,
    ReferenceField,
    PointField,
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
    person = ReferenceField("Person", required=True)


class Person(Document):
    faces = ListField(ReferenceField(Face))

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
