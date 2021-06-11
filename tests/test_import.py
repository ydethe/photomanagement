import os

from tqdm import tqdm
from mongoengine import connect

from PhotoManagement.db import Face, Photo, Person
from PhotoManagement.Image import import_image


# mongod --config /opt/homebrew/etc/mongod.conf --fork
connect("photo_mgt")

# Suppression d'un mois dans Mongo shell:
# db.photo.deleteMany({date_taken:{$gte: new Date('2020-05-01 00:00:00'),$lt:new Date('2020-06-01 00:00:00')}})
os.makedirs("miniatures", exist_ok=True)
# for (root, dirs, files) in tqdm(os.walk("tests/Mai2020")):
for (root, dirs, files) in tqdm(os.walk("tests/Mars2020")):
    for f in tqdm(files):
        pth = os.path.join(root, f)
        _, ext = os.path.splitext(pth)
        if ext.lower() in [".png", ".jpg", ".jpeg"]:
            photo = import_image(pth, match_persons=False)

# p = Person.objects(nom="Camille").first()
# p.showFaces()
# exit(0)

# Photo.showPhoto("60c11743a1e96f6b489df8f9", show_faces=True)
Photo.showPhoto("60c11748a1e96f6b489df903", show_faces=True)
exit(0)

# Face.exportAll()

# for p in tqdm(Person.objects):
#     p.saveFaces()

# for p in Photo.objects:
#     print(p.id)

# for b in Face.objects:
#     print(b.photo.id)
