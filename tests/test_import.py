import os

from tqdm import tqdm

from PhotoManagement.Photo import Photo
from PhotoManagement.Face import Face


# Suppression d'un mois dans Mongo shell:
# db.photo.deleteMany({date_taken:{$gte: new Date('2020-05-01 00:00:00'),$lt:new Date('2020-06-01 00:00:00')}})

# for (root, dirs, files) in tqdm(os.walk("tests/Mai2020")):
# for (root, dirs, files) in tqdm(os.walk("tests/Mars2020")):
#     for f in tqdm(files):
#         pth = os.path.join(root, f)
#         _, ext = os.path.splitext(pth)
#         if ext.lower() in [".png", ".jpg", ".jpeg"]:
#             photo = Photo.importFile(pth, recognize=False)

# photo = Photo.importFile("tests/Mars2020/Photo 20-03-14 11-15-11 0587.jpg")
# photo = Photo.importFile("tests/Mai2020/Photo 20-05-04 13-54-50 0940.jpg", recognize=True)


# p = Person.objects(nom="Camille").first()
# p.showFaces()
# exit(0)

# Photo.showPhoto("60c44c07023fb1c44484636f", show_faces=True)
# exit(0)

Face.exportAll()

# for p in tqdm(Person.objects):
#     p.saveFaces()

# for p in Photo.objects:
#     print(p.id)

# for b in Face.objects:
#     print(b.photo.id)
