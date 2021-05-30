import pickle
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
from PIL import Image, ImageDraw
import face_recognition
import numpy as np


# mongod --config /opt/homebrew/etc/mongod.conf --fork
connect("photo_mgt")


class Face(Document):
    blob = BinaryField()
    xleft = IntField()
    xright = IntField()
    ydown = IntField()
    yup = IntField()
    photo = ReferenceField("Photo")


class Photo(Document):
    file = StringField()
    place_taken = PointField()
    miniature = ImageField()
    date_taken = DateTimeField()
    faces = ListField(ReferenceField(Face))
    album = ReferenceField("Album")

    def showFaces(self):
        image = face_recognition.load_image_file(self.file)

        img = Image.fromarray(image, "RGB")
        img_with_red_box = img.copy()
        img_with_red_box_draw = ImageDraw.Draw(img_with_red_box)

        for face in self.faces:
            blob = pickle.loads(face.blob)

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
