import os

from tqdm import tqdm

from PhotoManagement.Photo import Photo
from PhotoManagement.Face import Face


# Suppression d'un mois dans Mongo shell:
# db.photo.deleteMany({date_taken:{$gte: new Date('2020-05-01 00:00:00'),$lt:new Date('2020-06-01 00:00:00')}})

# for (root, dirs, files) in tqdm(os.walk("tests/Mai2020")):
# for (root, dirs, files) in tqdm(os.walk("tests/Mars2020")):
# for f in tqdm(files):
#     pth = os.path.join(root, f)
#     _, ext = os.path.splitext(pth)
#     if ext.lower() in [".png", ".jpg", ".jpeg"]:
#         photo = Photo.importFile(pth, recognize=True)

pth = "tests/Mai2020/Photo 20-05-04 13-54-51 0944.jpg"
# pth="tests/Mai2020/Photo 20-05-04 13-54-50 0940.jpg"
# photo = Photo.importFile(pth,recognize=True)
# photo = Photo.objects(
#     original_path=pth
# ).first()
# for face in photo.faces:
#     if not face.person is None:
#         rec = face.person.getAirtableInformation()
#         print(rec["Nom complet"])

# p = Person.objects(nom="Camille").first()
# p.showFaces()
# exit(0)

Photo.showPhoto(original_path=pth, show_faces=True)
exit(0)

# Face.exportAll()

# for p in tqdm(Person.objects):
#     p.saveFaces()

# for p in Photo.objects:
#     print(p.id)

# for b in Face.objects:
#     print(b.photo.id)
