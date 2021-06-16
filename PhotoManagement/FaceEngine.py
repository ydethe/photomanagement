import io
from typing import List
import hashlib
from operator import le
from flask.scaffold import F

from retinaface import RetinaFace
from deepface.basemodels import ArcFace
from PIL import Image
import numpy as np

from PhotoManagement.db import Photo, Face


face_detector = RetinaFace.build_model()
face_recog = ArcFace.loadModel()
face_recog.load_weights("/Users/ydethe/.deepface/weights/arcface_weights.h5")


def detect_face(photo: Photo) -> List[Face]:
    buf = photo.photo.read()
    orig_img = Image.open(io.BytesIO(buf))
    orig_arr = np.array(orig_img)

    detec = RetinaFace.detect_faces(orig_arr, model=face_detector)

    faces = []
    for kd in detec.keys():
        # Coordinates of the face the picture
        left, upper, right, lower = detec[kd]["facial_area"]

        # Crop the picture to extract the face
        rect_face = orig_img.crop((left, upper, right, lower))

        # Resizing the face (112,112)
        # and adding black pixels if the extracted face is not square
        w = right - left
        h = lower - upper
        img = Image.new(mode="RGB", size=(112, 112), color=(0, 0, 0))
        if w > h:
            rect_face = rect_face.resize((112, (112 * h) // w))
            img.paste(rect_face, (0, 56 - (56 * h) // w))
        else:
            rect_face = rect_face.resize(((112 * w) // h, 112))
            img.paste(rect_face, (56 - (56 * w) // h, 0))

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

        face_db = Face(
            hash=h,
            embedding=embedding,
            left=left,
            right=right,
            lower=lower,
            upper=upper,
            photo=photo,
            manually_tagged=False,
            detection_score=detec[kd]["score"],
            # landmarks=detec[kd]["landmarks"],
        )
        face_db.save()

        faces.append(face_db)

    return faces
