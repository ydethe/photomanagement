import os
import yaml
from datetime import datetime
from mongoengine import connect, disconnect
import phonenumbers

from PhotoManagement import logger
from PhotoManagement.Face import Face
from PhotoManagement.Photo import Photo
from PhotoManagement.Person import Person


disconnect()
connect(host="mongodb://localhost:27017/photo_mgt")


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


Face.showPhotoForFace(hash="42e8bb4213b81d1e2589a9732c67b61709f458e219864dd5e189ee61")
# Face.showPhotoForFace(id="60c9f97087315ec5617a5423")
exit(0)

# Face.exportAll()
# exit(0)

clearLinkPersonFace()
root0 = "faces"

for root, dirs, files in os.walk(root0):
    nom = os.path.relpath(root, root0)
    if nom == ".":
        continue

    nom, aid = nom.split("_")

    q = Person.objects(airtable_id=aid)
    if q.count() == 0:
        pers = Person(airtable_id=aid)
        pers.save()
        print("Creating %s... " % nom, end="")
    else:
        pers = q.first()
        print("Updating %s... " % nom, end="")

    for f in files:
        face_hash, _ = os.path.splitext(f)
        face = Face.objects(hash=face_hash).first()
        if face is None:
            logger.warning(face_hash)
            continue
        face.affectToPersonAndSaveAll(pers)

    print("Done")
