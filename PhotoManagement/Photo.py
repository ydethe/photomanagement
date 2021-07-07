# Photo.py
import io
import os
from enum import Enum, unique
import hashlib
from typing import List
from datetime import datetime
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
import numpy as np
from tensorflow.python.keras.layers.merge import Add
from tqdm import tqdm
from mongoengine import signals
from PIL import Image, ImageDraw, ImageFont
from pkg_resources import require
from PIL.ExifTags import GPSTAGS, TAGS
from PIL.TiffImagePlugin import IFDRational
from retinaface import RetinaFace
from deepface.basemodels import ArcFace
from deepface.commons import distance as dst
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

from . import logger, db
from .config import Config
from .Face import Face
from .utils.db import handler
from .Address import Address, get_decimal_coordinates
from .Face import Face
from .Person import Person


def read_metadata(pth: str, write_md: bool = False) -> dict:
    im = Image.open(pth)
    exif_data = im._getexif()
    _, fn = os.path.split(pth)
    bn, _ = os.path.splitext(fn)

    if write_md:
        os.makedirs("md", exist_ok=True)
        f_md = open("md/metadata_%s.txt" % fn, "src_w")
        f_md.write("%s\n" % pth)
        f_md.write("%s\n" % exif_data)
        im.close()

    if exif_data is None:
        exif_data = {}

    lkeys = list(exif_data.keys())
    for key in lkeys:
        name = TAGS.get(key, key)
        exif_data[name] = exif_data.pop(key)

    if "GPSInfo" in exif_data:
        lkeys = list(exif_data["GPSInfo"].keys())
    elif "34853" in exif_data:
        lkeys = list(exif_data["34853"].keys())
        exif_data["GPSInfo"] = {}
    else:
        lkeys = []
        exif_data["GPSInfo"] = {}

    for key in lkeys:
        name = GPSTAGS.get(key, key)
        exif_data["GPSInfo"][name] = exif_data["GPSInfo"].pop(key)

    orig_exif = stringify_keys(exif_data)

    if not "Orientation" in exif_data.keys():
        exif_data["Orientation"] = 1

    if "DateTimeOriginal" in exif_data.keys():
        date_time_str = exif_data["DateTimeOriginal"]
        # date_time_str='2020:04:02 12:58:12'
        exif_data["InferredDateTime"] = False
        dt = datetime.strptime(date_time_str, "%Y:%m:%d %H:%M:%S")
    else:
        # bn="Photo 20-03-13 17-53-52 0558"
        exif_data["InferredDateTime"] = True
        dt = datetime.strptime(bn, "Photo %y-%m-%d %H-%M-%S %f")

    exif_data["DateTimeOriginal"] = dt

    lat, lon = get_decimal_coordinates(exif_data["GPSInfo"])
    exif_data["GPSInfo"]["Latitude"] = lat
    exif_data["GPSInfo"]["Longitude"] = lon

    if write_md:
        f_md.write("%s\n" % exif_data)
        f_md.close()

    return orig_exif, exif_data


def crop_face(img: Image, height: int, force_square=True) -> Image:
    src_w, src_h = img.size
    sze_h = height
    sze_w = (sze_h * src_w) // src_h

    if force_square:
        tgt_h = height
        tgt_w = height
    else:
        tgt_h = height
        tgt_w = tgt_h * src_w / src_h

    rect_face = img.resize((sze_w, sze_h))

    # Resizing the face
    # and adding black pixels if the extracted face is not square
    img = Image.new(mode="RGB", size=(tgt_w, tgt_h), color=(0, 0, 0))
    if sze_w > sze_h:
        img.paste(rect_face, (0, tgt_w // 2 - sze_h // 2))
    else:
        img.paste(rect_face, (tgt_h // 2 - sze_w // 2, 0))

    return img


def stringify_keys(md: dict) -> dict:
    ret = {}
    for k in md.keys():
        sk = str(k)
        if isinstance(md[k], dict):
            sv = stringify_keys(md[k])
        else:
            sv = md[k]
            if isinstance(sv, IFDRational):
                sv = float(sv)
            elif hasattr(sv, "__iter__") and not isinstance(sv, str):
                svl = []
                for svk in sv:
                    if isinstance(svk, IFDRational):
                        if svk.denominator == 0:
                            svk = np.nan
                        else:
                            svk = float(svk)
                    svl.append(svk)
                sv = svl

        ret[sk] = sv

    return ret


face_detector = RetinaFace.build_model()
face_recog = ArcFace.loadModel()
face_recog.load_weights("/Users/ydethe/.deepface/weights/arcface_weights.h5")


def detect_face(photo: Image) -> List[dict]:
    orig_arr = np.array(photo)

    detec = RetinaFace.detect_faces(orig_arr, model=face_detector)
    if not hasattr(detec, "keys"):
        detec = {}

    faces = []
    for kd in detec.keys():
        # Coordinates of the face the picture
        left, upper, right, lower = detec[kd]["facial_area"]

        # Crop the picture to extract the face
        rect_face = photo.crop((left, upper, right, lower))

        # Resizing the face (112,112)
        img = crop_face(rect_face, height=112, force_square=True)

        # Hash of the face
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf = buf.getvalue()
        h = hashlib.sha224(buf).hexdigest()

        # Embedding of the face
        img = np.array(img, dtype=np.float32)
        img_pixels = np.expand_dims(img, axis=0)
        img_pixels /= 255  # normalize input in [0, 1]
        embedding = face_recog.predict(img_pixels)[0]

        face_db = dict(
            hash=h,
            embedding=embedding,
            left=left,
            right=right,
            lower=lower,
            upper=upper,
            manually_tagged=False,
            detection_score=detec[kd]["score"],
            # landmarks=detec[kd]["landmarks"],
        )
        faces.append(face_db)

    logger.debug("%i faces detected" % len(faces))

    return faces


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

    meta = {"ordering": ["date_taken"]}

    @classmethod
    def showPhoto(cls, show_faces=False, **kwargs):
        photo = cls.objects(**kwargs).first()
        image = photo.photo.read()
        img = Image.open(io.BytesIO(image))
        font = ImageFont.truetype("Arial Unicode.ttf", size=15)

        if show_faces:
            # Drawing a red rectangle on the photo to locate the person
            img_with_red_box_draw = ImageDraw.Draw(img)
            for face in photo.faces:
                if face.manually_tagged:
                    color = "green"
                else:
                    color = "red"

                img_with_red_box_draw.rectangle(
                    [(face.left, face.upper), (face.right, face.lower)],
                    outline=color,
                    width=3,
                )
                if not face.person is None:
                    rec = face.person.complete_name
                    nom = rec["Nom complet"]
                else:
                    nom = "Unknown"
                img_with_red_box_draw.text(
                    (face.left, face.lower), nom, font=font, fill=color
                )

        img.show()

    def show(self, show_faces=True):
        image = self.photo.read()
        img = Image.open(io.BytesIO(image))

        if show_faces:
            img_with_red_box_draw = ImageDraw.Draw(img)

            for face in self.faces:
                if face.manually_tagged:
                    color = "green"
                else:
                    color = "red"
                img_with_red_box_draw.rectangle(
                    [(face.left, face.upper), (face.right, face.lower)],
                    outline=color,
                    width=3,
                )

        img.show()

    @classmethod
    def importFile(cls, pth: str, recognize: bool = False) -> "Photo":
        face_dst_dir = "faces"
        os.makedirs(face_dst_dir, exist_ok=True)

        logger.info(72 * "=")
        logger.info(pth)

        # ======================
        # Lecture des metadata
        # ======================
        orig_exif, metadata = read_metadata(pth)
        gps_info = metadata.get("GPSInfo", {})
        lat = gps_info.get("Latitude", None)
        lon = gps_info.get("Longitude", None)
        alt = gps_info.get("GPSAltitude", 0)
        if not lon is None and not lat is None:
            place_taken = Address.fromLatLonAlt(lat, lon, alt)
        else:
            logger.warning("No location data")
            place_taken = None
        inferred_dt = metadata["InferredDateTime"]
        date_taken = metadata.get("DateTimeOriginal", None)

        # ======================
        # Photo creation
        # ======================
        img = Image.open(pth)
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        src_h = hashlib.sha224(buf.getvalue()).hexdigest()

        if cls.objects(hash=src_h).count() > 0:
            dup = cls.objects(hash=src_h).first()
            logger.warning("Duplicate photo (skipping):")
            logger.warning("%s" % pth)
            logger.warning("%s" % dup.original_path)
            return

        if date_taken is None:
            photo = cls(
                hash=src_h,
                original_exif=orig_exif,
                inferred_date=inferred_dt,
                original_path=pth,
            )
            logger.warning("No date and time data")
        else:
            photo = cls(
                hash=src_h,
                original_exif=orig_exif,
                inferred_date=inferred_dt,
                original_path=pth,
                date_taken=date_taken,
            )

        if not place_taken is None:
            photo.save()
            photo.place_taken = place_taken
            place_taken.photos.append(photo)
            place_taken.save()

        # ======================
        # Orientation correction
        # ======================
        # angle – In degrees counter clockwise
        if metadata["Orientation"] == 8:
            angle = 90
        elif metadata["Orientation"] == 3:
            angle = 180
        elif metadata["Orientation"] == 6:
            angle = -90
        else:
            angle = 0

        if angle != 0:
            logger.debug("Rotated a=%i deg, %s" % (angle, photo.id))
            img = img.rotate(angle=angle)

        # ======================
        # Miniature creation
        # ======================
        src_w, src_h = img.size
        if src_w < src_h:
            mini = img.resize(
                size=(200, 200),
                resample=Image.HAMMING,
                box=(0, (src_h - src_w) // 2, src_w, src_w),
            )
        else:
            mini = img.resize(
                size=(200, 200),
                resample=Image.HAMMING,
                box=((src_w - src_h) // 2, 0, src_h, src_h),
            )

        # ======================
        # Enregistrement photo et miniature
        # ======================
        with io.BytesIO() as buf:
            mini.save(buf, format="JPEG")
            photo.miniature.replace(buf, filename=pth)

        with io.BytesIO() as buf:
            img.save(buf, format="JPEG")
            photo.photo.replace(buf, filename=pth)

        photo.save()

        # ======================
        # Faces detection
        # ======================
        lfaces = detect_face(img)
        for face_info in lfaces:
            q = Face.objects(hash=face_info["hash"])
            if q.count() > 0:
                face = q.first()
                logger.debug("Found Face already existing")
            else:
                face = Face(photo=photo, **face_info)
                face.save()
            if recognize:
                matching, corr = face.recognize_face()
                if not matching is None:
                    face.person = matching
                    face.recognition_score = corr
                    face.save()
            photo.faces.append(face)
        photo.save()

        return photo

    def getB64Miniature(self) -> bytes:
        image = self.miniature.read()
        b64 = base64.b64encode(image)
        return b64

    @property
    def date_elements(self):
        photo_year = self.date_taken.year
        photo_month = self.date_taken.month
        photo_month_name = datetime.strftime(self.date_taken, "%B")
        photo_day = self.date_taken.day
        photo_id = self.id
        return photo_year, photo_month, photo_month_name, photo_day, photo_id
