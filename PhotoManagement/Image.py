from datetime import datetime
import os
import io
import hashlib
import logging
from datetime import datetime
from typing import Tuple

import numpy as np

# import face_recognition
from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS
from PIL.TiffImagePlugin import IFDRational
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
import what3words
import geocoder

from .db import Face, Photo, Person, Address
from . import am
from .config import Config


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
                        svk = float(svk)
                    svl.append(svk)
                sv = svl

        ret[sk] = sv

    return ret


def get_decimal_coordinates(info: dict) -> Tuple[float]:
    for key in ["Latitude", "Longitude"]:
        if "GPS" + key in info and "GPS" + key + "Ref" in info:
            e = info["GPS" + key]
            ref = info["GPS" + key + "Ref"]

            s = 0
            mul = [1, 60, 3600]
            for k, m in enumerate(mul):
                s += float(e[k]) / m

            info[key] = s * (-1 if ref in ["S", "W"] else 1)

    if "Latitude" in info and "Longitude" in info:
        return [info["Latitude"], info["Longitude"]]
    else:
        return None, None


def getAddress(lat: float, lon: float, alt: float) -> Address:
    """

    >>> getAddress(43.60467117912294,1.4415632156260192,0)
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
    w3wgc = what3words.Geocoder("642RI3LY")
    res = w3wgc.convert_to_3wa(what3words.Coordinates(lat, lon))
    q = Address.objects(w3w=res["words"])
    if q.count() > 0:
        return q.first()

    g = geocoder.osm([lat, lon], method="reverse")
    dat = g.geojson["features"][0]["properties"]["raw"]["address"]

    if "city" in dat.keys():
        ville = dat["city"]
    elif "village" in dat.keys():
        ville = dat["village"]
    elif "town" in dat.keys():
        ville = dat["town"]

    try:
        addr = Address(
            ville=ville,
            pays=dat["country"],
            rue=dat.get("road", ""),
            numero=int(dat.get("house_number", "0")),
            code_postal=dat["postcode"],
            latitude=lat,
            longitude=lon,
            altitude=alt,
            w3w=res["words"],
        )
    except Exception as e:
        print(dat)
        exit(1)
    addr.save()
    return addr


def read_metadata(pth: str, write_md: bool = False) -> dict:
    im = Image.open(pth)
    exif_data = im._getexif()
    _, fn = os.path.split(pth)
    bn, _ = os.path.splitext(fn)

    if write_md:
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


def import_image(pth: str, recog_engine=None) -> Photo:
    face_dst_dir = "faces"
    os.makedirs(face_dst_dir, exist_ok=True)

    log = logging.getLogger("photomgt_logger")

    log.info(72 * "=")
    log.info(pth)

    # ======================
    # Lecture des metadata
    # ======================
    orig_exif, metadata = read_metadata(pth)
    gps_info = metadata.get("GPSInfo", {})
    lat = gps_info.get("Latitude", None)
    lon = gps_info.get("Longitude", None)
    alt = gps_info.get("GPSAltitude", 0)
    if not lon is None and not lat is None:
        place_taken = getAddress(lat, lon, alt)
    else:
        log.warning("No location data")
        place_taken = None
    inferred_dt = metadata["InferredDateTime"]
    date_taken = metadata.get("DateTimeOriginal", None)

    # ======================
    # Photo creation
    # ======================
    img = Image.open(pth)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    h = hashlib.sha224(buf.getvalue()).hexdigest()

    if Photo.objects(hash=h).count() > 0:
        dup = Photo.objects(hash=h).first()
        log.warning("Duplicate photo (skipping):")
        log.warning("%s" % pth)
        log.warning("%s" % dup.original_path)
        return

    if date_taken is None:
        photo = Photo(
            hash=h,
            original_exif=orig_exif,
            inferred_date=inferred_dt,
            original_path=pth,
        )
        log.warning("No date and time data")
    else:
        photo = Photo(
            hash=h,
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
        log.debug("Rotated a=%i deg, %s" % (angle, photo.id))
        img = img.rotate(angle=angle)

    # ======================
    # Miniature creation
    # ======================
    w, h = img.size
    if w < h:
        mini = img.resize(
            size=(200, 200), resample=Image.HAMMING, box=(0, (h - w) // 2, w, w)
        )
    else:
        mini = img.resize(
            size=(200, 200), resample=Image.HAMMING, box=((w - h) // 2, 0, h, h)
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
    # image = np.array(img)

    # face_locations = face_recognition.face_locations(image)
    # face_encodings = face_recognition.face_encodings(image, face_locations)

    # lfaces = []
    # for blob, loc in zip(face_encodings, face_locations):
    #     # ((Upper left x, upper left y), (lower right x, lower right y)
    #     # (loc[3], loc[0]), (loc[1], loc[2])
    #     yup, xright, ydown, xleft = loc

    #     # Creating a miniature of the person's face
    #     face_img = img.resize(
    #         size=(xright - xleft, ydown - yup),
    #         box=(xleft, yup, xright, ydown),
    #     )
    #     buf = io.BytesIO()
    #     face_img.save(buf, format="JPEG")
    #     buf = buf.getvalue()
    #     h = hashlib.sha224(buf).hexdigest()
    #     # face_img.save("%s/%s.jpg" % (face_dst_dir, h))

    #     # Test si une face avec le meme hash existe
    #     q = Face.objects(hash=h)
    #     if q.count() > 0:
    #         log.warning("Duplicate face hash : %s" % h)
    #         face = q.first()
    #         face.photo = photo
    #         face.manually_tagged = False
    #     else:
    #         face = Face(
    #             blob=blob,
    #             hash=h,
    #             xleft=xleft,
    #             yup=yup,
    #             xright=xright,
    #             ydown=ydown,
    #             photo=photo,
    #             manually_tagged=False,
    #         )

    #     face.save()

    #     lfaces.append(face)

    #     if not recog_engine is None:
    #         log.debug("Recognition face id=%s" % face.id)

    #         pid, d = recog_engine.testBlob(blob)

    #         matching_person = Person.objects(id=pid).first()
    #         aid = matching_person.airtable_id
    #         if aid.startswith("rec"):
    #             rec = am.get_rec_by_id("pers_table", aid)
    #             matching_name = rec["fields"]["Nom complet"]
    #         else:
    #             matching_name = aid
    #         log.debug("Found person (%s):\td=%.4f" % (matching_name, d))
    #         face.person = matching_person
    #         face.save()
    #         matching_person.faces.append(face)
    #         matching_person.save()

    # photo.faces = lfaces
    # photo.save()

    return photo


if __name__ == "__main__":
    pth = "tests/Mars2020/Photo 20-03-31 17-58-57 0684.jpg"
    read_metadata(pth)
