import pickle
import hashlib
import os
import logging
from re import M

from tqdm import tqdm
import numpy as np
import face_recognition
from PIL import Image, ImageDraw
from mongoengine import connect
import mongoshapes as ms

from PhotoManagement.db import Face, Photo, Person
from PhotoManagement.Image import read_metadata


def import_image(pth: str, match_persons=True) -> Photo:
    log = logging.getLogger("photomgt_logger")

    log.info(72 * "=")
    log.info(pth)
    metadata = read_metadata(pth)
    gps_info = metadata.get("GPSInfo", {})
    lat = gps_info.get("Latitude", None)
    lon = gps_info.get("Longitude", None)
    alt = gps_info.get("GPSAltitude", 0)
    if not lon is None and not lat is None:
        place_taken = ms.Point([lon, lat, alt])
    else:
        log.warning("No location data")
        place_taken = None
    date_taken = metadata.get("DateTimeOriginal", None)
    # place_taken = {"type": "Point", "coordinates": [lon, lat,alt]}
    image = face_recognition.load_image_file(pth)

    with open(pth, "rb") as afile:
        buf = afile.read()
        h = hashlib.sha224(buf).hexdigest()

    if date_taken is None:
        photo = Photo(hash=h, original_path=pth)
        log.warning("No date and time data")
    else:
        photo = Photo(
            hash=h, original_path=pth, date_taken=metadata["DateTimeOriginal"]
        )
    if not place_taken is None:
        photo.place_taken = place_taken
    photo.photo.replace(open(pth, "rb"), filename=pth)
    photo.save()

    # ======================
    # Miniature creation
    # ======================
    img = Image.fromarray(image, "RGB")
    w, h = img.size
    if w < h:
        img = img.resize(
            size=(200, 200), resample=Image.HAMMING, box=(0, (h - w) // 2, w, w)
        )
    else:
        img = img.resize(
            size=(200, 200), resample=Image.HAMMING, box=((w - h) // 2, 0, h, h)
        )
    img.save("miniatures/%s.jpg" % photo.id)
    my_mini = open("miniatures/%s.jpg" % photo.id, "rb")
    photo.miniature.replace(my_mini, filename=pth)
    photo.save()

    # ======================
    # Faces detection
    # ======================
    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)

    lfaces = []
    for blob, loc in zip(face_encodings, face_locations):
        # ((Upper left x, upper left y), (lower right x, lower right y)
        # (loc[3], loc[0]), (loc[1], loc[2])
        yup, xright, ydown, xleft = loc
        face = Face(
            blob=pickle.dumps(blob),
            xleft=xleft,
            yup=yup,
            xright=xright,
            ydown=ydown,
            photo=photo,
        )
        face.save()
        lfaces.append(face)

        if match_persons:
            Jmin = 0
            matching_person = None
            for p in Person.objects:
                test_blobs = [pickle.loads(x.blob) for x in p.faces]
                results = face_recognition.face_distance(test_blobs, blob)
                J = np.sum(results ** 2)
                if matching_person is None or J < Jmin:
                    Jmin = J
                    matching_person = p

            if matching_person is None or Jmin > 0.5:
                log.info("No Person found %.4f" % Jmin)
                # matching_person = Person()
                # matching_person.save()
                # face.person = matching_person
                # face.save()
                # matching_person.faces = [face]
                # matching_person.save()
            else:
                log.info("Found person (%s):\t%.4f" % (matching_person.nom, Jmin))
                face.person = matching_person
                face.save()
                matching_person.faces.append(face)
                matching_person.save()

    photo.faces = lfaces
    photo.save()

    return photo


# mongod --config /opt/homebrew/etc/mongod.conf --fork
connect("photo_mgt")

# pth = "tests/Mars2020/Photo 20-03-13 17-53-56 0565.jpg"
# pth = "tests/Mars2020/Photo 20-03-14 10-58-42 0572.jpg"
# pth = "tests/Mars2020/Photo 20-03-14 10-58-45 0573.jpg"
# pth = "tests/Mars2020/Photo 20-03-13 17-53-52 0558.jpg"
# photo = import_image(pth)
# photo.showFaces()

os.makedirs("miniatures", exist_ok=True)
# for (root, dirs, files) in os.walk("tests/Mai2020"):
for (root, dirs, files) in tqdm(os.walk("tests/Mars2020")):
    for f in tqdm(files):
        pth = os.path.join(root, f)
        _, ext = os.path.splitext(pth)
        if ext.lower() in [".png", ".jpg", ".jpeg"]:
            photo = import_image(pth, match_persons=False)

# p = Person.objects(nom="Camille").first()
# p.showFaces()
# exit(0)

# Photo.showPhoto("60c0e4b3702259dfc562911d")
# exit(0)

# for p in tqdm.tqdm(Person.objects):
#     p.saveFaces()

# for p in Photo.objects:
#     print(p.id)

# for b in Face.objects:
#     print(b.photo.id)
