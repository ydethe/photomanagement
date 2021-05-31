import pickle

import face_recognition
from PIL import Image, ImageDraw
from mongoengine import connect

from db import Face, Photo


def import_image(pth):
    image = face_recognition.load_image_file(pth)
    img = Image.fromarray(image, "RGB")
    w,h=img.size
    if w<h:
        img=img.resize(size=(200,200),resample=Image.HAMMING, box=(0,(h-w)//2,w,w))
    else:
        img=img.resize(size=(200,200),resample=Image.HAMMING, box=((w-h)//2,0,h,h))
    img.save('mini.jpg')
    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)

    photo = Photo(file=pth)
    my_mini=open('mini.jpg','rb')
    photo.miniature.replace(my_mini, filename=pth)
    photo.save()
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

    photo.faces = lfaces
    photo.save()

    return photo


# mongod --config /opt/homebrew/etc/mongod.conf --fork
connect("photo_mgt")

# pth = "Mars2020/Photo 20-03-13 17-53-56 0565.jpg"
# pth = "Mars2020/Photo 20-03-14 10-58-42 0572.jpg"
pth = "Mars2020/Photo 20-03-14 10-58-45 0573.jpg"
photo = import_image(pth)
photo.showFaces()
