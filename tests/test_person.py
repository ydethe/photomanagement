import os
import yaml

from mongoengine import connect

from PhotoManagement import logger
from PhotoManagement.db import Face, Photo, Person

# from PhotoManagement.Image import read_metadata


connect("photo_mgt")


def clearLinkPersonFace():
    for face in Face.objects():
        face.person = None
        face.manually_tagged = False
        face.save()
    Person.objects().delete()


# clearLinkPersonFace()
# exit(0)

# Face.exportAll()
# exit(0)

# clearLinkPersonFace()
root0 = "faces"

for root, dirs, files in os.walk(root0):
    nom = os.path.relpath(root, root0)
    if nom == ".":
        continue

    with open(os.path.join(root, "info.yml"), "r") as f:
        info = yaml.load(f, Loader=yaml.FullLoader)

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
