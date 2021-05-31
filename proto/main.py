import pickle
import hashlib

import face_recognition
from PIL import Image, ImageDraw
from mongoengine import connect

from db import Face, Photo
from Image import read_metadata


def import_image(pth):
    metadata = read_metadata(pth)
    gps_info = metadata.get("GPSInfo", {})
    lat = gps_info.get("Latitude", None)
    lon = gps_info.get("Longitude", None)
    place_taken = {"type": "Point", "coordinates": [lon, lat]}
    image = face_recognition.load_image_file(pth)
    
    with open(pth, 'rb') as afile:
        buf = afile.read()
        h = hashlib.sha224(buf).hexdigest()

    photo = Photo(
        file=pth,
        hash=h,
        place_taken=place_taken,
        date_taken=metadata["DateTimeOriginal"],
    )
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
    img.save("%s.jpg" % photo.id)
    my_mini = open("%s.jpg" % photo.id, "rb")
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

    photo.faces = lfaces
    photo.save()

    return photo


# mongod --config /opt/homebrew/etc/mongod.conf --fork
connect("photo_mgt")

# pth = "Mars2020/Photo 20-03-13 17-53-56 0565.jpg"
# pth = "Mars2020/Photo 20-03-14 10-58-42 0572.jpg"
pth = "Mars2020/Photo 20-03-14 10-58-45 0573.jpg"
photo = import_image(pth)
photo.showFaces()

for p in Photo.objects:
    print(p.id)
