import os
import yaml
from datetime import datetime
from mongoengine import connect
import phonenumbers

from PhotoManagement import logger
from PhotoManagement.db import Face, Photo, Person

# from PhotoManagement.Image import read_metadata


connect("photo_mgt")


def fmt_tel(s):
    try:
        if not s.startswith("+") and not s.startswith("00"):
            z = phonenumbers.parse(s, "FR")
        elif s.startswith("00"):
            z = phonenumbers.parse("+" + s[2:])
        elif s.startswith("+"):
            z = phonenumbers.parse(s)
        else:
            pass

        if not phonenumbers.is_valid_number(z):
            return ""

        s = phonenumbers.format_number(z, phonenumbers.PhoneNumberFormat.INTERNATIONAL)

        return s
    except Exception as e:
        logger.error(e)
        return ""


def clearLinkPersonFace():
    for face in Face.objects():
        face.person = None
        face.manually_tagged = False
        face.save()
    Person.objects().delete()


# Face.exportAll()
# exit(0)

clearLinkPersonFace()
root0 = "faces"

for root, dirs, files in os.walk(root0):
    nom = os.path.relpath(root, root0)
    if nom == ".":
        continue

    with open(os.path.join(root, "info.yml"), "r") as f:
        info = yaml.load(f, Loader=yaml.FullLoader)
    info["mobile_perso"] = fmt_tel(info["mobile_perso"])
    info["mobile_pro"] = fmt_tel(info["mobile_pro"])
    info["fix_pro"] = fmt_tel(info["fix_pro"])
    info["date_birth"] = datetime.strptime(info["date_birth"], "%d/%m/%Y")

    pers = Person(**info)
    pers.save()
    print("Created %s... " % nom, end="")

    for f in files:
        face_hash, _ = os.path.splitext(f)
        face = Face.objects(hash=face_hash).first()
        if face is None:
            logger.error(face_hash)
            exit(1)
        face.affectToPersonAndSaveAll(pers)

    print("Done")
