import os

from mongoengine import connect

from PhotoManagement.db import Face, Photo, Person

# from PhotoManagement.Image import read_metadata


connect("photo_mgt")


def clearLinkPersonFace():
    for face in Face.objects():
        face.person = None
        face.manually_tagged = True
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

    pers = Person(nom=nom)
    pers.save()
    print("Created %s... " % nom, end="")

    for f in files:
        face_id, _ = os.path.splitext(f)
        face = Face.objects(id=face_id).first()
        face.affectToPersonAndSaveAll(pers)

    print("Done")
