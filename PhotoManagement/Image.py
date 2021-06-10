from datetime import datetime
import os
import pickle
import hashlib
import logging
from datetime import datetime
from typing import Tuple

import numpy as np
import mongoshapes as ms
import face_recognition
from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

from PhotoManagement.db import Face, Photo, Person


def get_decimal_coordinates(info: dict) -> Tuple[float]:
    for key in ["Latitude", "Longitude"]:
        if "GPS" + key in info and "GPS" + key + "Ref" in info:
            e = info["GPS" + key]
            ref = info["GPS" + key + "Ref"]

            s = 0
            mul = [1, 60, 3600]
            for k, m in enumerate(mul):
                s += float(e[0]) / m

            info[key] = s * (-1 if ref in ["S", "W"] else 1)

    if "Latitude" in info and "Longitude" in info:
        return [info["Latitude"], info["Longitude"]]
    else:
        return None, None


def getAddress(lat: float, lon: float) -> dict:
    """

    >>> getAddress(43.60467117912294,1.4415632156260192)
    {'city': 'Toulouse',
     'country': 'France',
     'country_code': 'fr',
     'county': 'Haute-Garonne',
     'municipality': 'Toulouse',
     'neighbourhood': 'Place Occitane',
     'postcode': '31000',
     'road': 'Rue Jean-Antoine Romiguières',
     'shop': 'Jean Claude Aubry Romiguières',
     'state': 'Occitanie',
     'suburb': 'Toulouse Centre'}

    """
    g = geocoder.osm([lat, lon], method="reverse")
    addr = g.geojson["features"][0]["properties"]["raw"]["address"]
    return addr


def read_metadata(pth: str) -> dict:
    im = Image.open(pth)
    exif_data = im._getexif()
    _, fn = os.path.split(pth)
    bn, _ = os.path.splitext(fn)

    os.makedirs("md", exist_ok=True)
    f_md = open("md/metadata_%s.txt" % fn, "w")
    f_md.write("%s\n" % pth)
    f_md.write("%s\n" % exif_data)
    im.close()

    if exif_data is None:
        exif_data = {}

    lkeys = list(exif_data.keys())
    for key in lkeys:
        name = TAGS.get(key, key)
        exif_data[name] = exif_data.pop(key)

    if "DateTimeOriginal" in exif_data.keys():
        date_time_str = exif_data["DateTimeOriginal"]
        # date_time_str='2020:04:02 12:58:12'
        exif_data["InferredDateTime"] = True
        dt = datetime.strptime(date_time_str, "%Y:%m:%d %H:%M:%S")
    else:
        # bn="Photo 20-03-13 17-53-52 0558"
        exif_data["InferredDateTime"] = False
        dt = datetime.strptime(bn, "Photo %y-%m-%d %H-%M-%S %f")

    exif_data["DateTimeOriginal"] = dt

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

    lat, lon = get_decimal_coordinates(exif_data["GPSInfo"])
    exif_data["GPSInfo"]["Latitude"] = lat
    exif_data["GPSInfo"]["Longitude"] = lon

    f_md.write("%s\n" % exif_data)
    f_md.close()

    return exif_data


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
    inferred_dt = metadata["InferredDateTime"]
    date_taken = metadata.get("DateTimeOriginal", None)
    # place_taken = {"type": "Point", "coordinates": [lon, lat]}
    image = face_recognition.load_image_file(pth)

    with open(pth, "rb") as afile:
        buf = afile.read()
        h = hashlib.sha224(buf).hexdigest()

    if Photo.objects(hash=h).count() > 0:
        dup = Photo.objects(hash=h).first()
        log.warning("Duplicate photo :")
        log.warning("s" % pth)
        log.warning("s" % dup.original_path)
        return

    if date_taken is None:
        photo = Photo(hash=h, inferred_date=inferred_dt, original_path=pth)
        log.warning("No date and time data")
    else:
        photo = Photo(
            hash=h, inferred_date=inferred_dt, original_path=pth, date_taken=date_taken
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


if __name__ == "__main__":
    pth = "tests/Mars2020/Photo 20-03-31 17-58-57 0684.jpg"
    read_metadata(pth)
