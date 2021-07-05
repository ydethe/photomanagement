# Face.py
import io
import os
from enum import Enum, unique
import base64

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
from PIL import Image, ImageDraw, ImageFont
from pkg_resources import require
from deepface.commons import distance as dst

from . import logger, db, am
from .utils.db import handler
from .Person import Person


@handler(signals.post_delete)
def face_suppressed(sender, document):
    if not document.photo is None and document in document.photo.faces:
        logger.debug(
            "Suppress face %s from photo %s" % (document.id, document.photo.id)
        )
        document.photo.faces.remove(document)
        document.photo.save()

    if not document.person is None and document in document.person.faces:
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
    recognition_score = FloatField()
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

    @property
    def size(self) -> int:
        return max(self.right - self.left, self.lower - self.upper)

    def getImage(self, lower_margin: int = 0) -> Image:
        image = self.photo.photo.read()
        img = Image.open(io.BytesIO(image))

        # Creating a miniature of the person's face
        mini = img.crop((self.left, self.upper, self.right, self.lower + lower_margin))

        return mini

    def getB64Image(self) -> bytes:
        img = self.getImage()
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        b64 = base64.b64encode(buf.getbuffer())
        return b64

    def showPhoto(self):
        image = self.photo.photo.read()
        img = Image.open(io.BytesIO(image))

        # Drawing a red rectangle on the photo to locate the person
        img_with_red_box_draw = ImageDraw.Draw(img)
        img_with_red_box_draw.rectangle(
            [(self.left, self.upper), (self.right, self.lower)], outline="red", width=3,
        )

        img.show()

    def show(self, text=""):
        mini = self.getImage(lower_margin=40)
        if self.manually_tagged:
            color = "green"
        else:
            color = "red"

        font = ImageFont.truetype("Arial Unicode.ttf", size=15)
        img_with_red_box_draw = ImageDraw.Draw(mini)
        img_with_red_box_draw.text(
            (0, self.lower - self.upper), text, font=font, fill=color
        )
        mini.show()

    def affectToPersonAndSaveAll(self, person):
        person.faces.append(self)
        person.save()

        if not self.person is None and self in self.person.faces:
            self.person.faces.remove(self)
            self.person.save()

        self.person = person
        self.manually_tagged = True
        self.save()

    def recognize(self) -> Person:
        logger.debug("Testing face hash %s" % self.hash)

        if self.size < 40:
            logger.debug("Face too small : %i" % self.size)
            return None, None

        euclideL2_th = 1.1315718048269017

        dmin_pers = None
        matching = None
        test_emb = self.embedding
        for pers in Person.objects():
            pers_info = pers.complete_name

            dmin_face = None
            for face in pers.faces:
                emb = face.embedding
                d = dst.findEuclideanDistance(
                    dst.l2_normalize(emb), dst.l2_normalize(test_emb)
                )
                if dmin_face is None or (d < dmin_face and d < euclideL2_th):
                    dmin_face = d

            # if not dmin_face is None:
            #     logger.debug("%s\t%.4f" % (pers_info, dmin_face))

            if not dmin_face is None and (dmin_pers is None or dmin_face < dmin_pers):
                dmin_pers = dmin_face
                matching = pers
                matching_info = pers_info

        logger.debug("--> Found '%s',\t%.4f" % (matching_info, dmin_pers))
        logger.debug(72 * "-")

        return matching, dmin_pers
