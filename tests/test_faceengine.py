from PhotoManagement.db import Photo
from PhotoManagement.FaceEngine import detect_face
from PhotoManagement.Image import import_image


# https://sefiks.com/2020/12/14/deep-face-recognition-with-arcface-in-keras-and-python/
pth = "tests/Mai2020/Photo 20-05-04 13-54-50 0940.jpg"
photo = import_image(pth)
# photo = Photo.objects(original_path=pth).first()
# lfaces = detect_face(photo)

recog_th = 1.1315718048269017
