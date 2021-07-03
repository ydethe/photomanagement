from pkg_resources import require
from datetime import datetime

from PhotoManagement.Person import Person
import time
import base64
import io

from flask import (
    render_template,
    request,
    flash,
    redirect,
    url_for,
    Markup,
)

from ...AirtableManager import AirtableManager
from ... import logger
from ...config import Config
from . import photo_bp
from ...Photo import Photo
from ...Face import Face


# 2020-04-08 21:32:50
date_fmt="%Y/%m/%d %H:%M:%S"

def updateFaces(data: dict, pidList: list) -> str:
    # ImmutableMultiDict([('photo_id', '60d4db7bd9685a94e51b3d25'), ('input-yann-blaudin-de-the', 'alix-de-chanterac'), ('input-ines-blaudin-de-the', 'ines-blaudin-de-the')])
    print(data)
    # print(pidList)
    # photo_id = data.get("photo_id", None)
    for k in data.keys():
        v = data[k]
        if k == "photo_id":
            photo = Photo.objects(id=v).first()
            nphoto = (
                Photo.objects(date_taken__gt=photo.date_taken)
                .order_by("date_taken")
                .first()
            )
            next_photo_id = nphoto.id
            continue
        elif k == "photo_lat":
            continue
        elif k == "photo_lon":
            continue
        elif k == "photo_alt":
            continue
        elif k == "photo_date":
            date_taken=datetime.strptime(v, date_fmt)
            continue

        face_id = k[6:]
        qf = Face.objects(id=face_id)
        if qf.count() != 1:
            logger.error("Face id unknown %s" % face_id)
            face = None
        else:
            face = qf.first()

        if v == "supp" and not face is None:
            face = qf.first()
            face.delete()
        else:
            if v.startswith("S"):
                pers_id = v[1:]
                tag_auto = True
            else:
                pers_id = v
                tag_auto = False

            qp = Person.objects(id=pers_id)
            if qp.count() != 1:
                logger.error("Person id unknown %s" % pers_id)
                pers = None
            else:
                pers = qp.first()
                logger.info("Face id %s affected to %s" % (face_id, pers.complete_name))
                face.affectToPersonAndSaveAll(pers)
                face.manually_tagged = not tag_auto
                face.save()

    return next_photo_id


@photo_bp.route("/", methods=["POST", "GET"])
def photo():
    personslist = ["Inconnu"]
    pidList = [""]
    for pers in Person.objects():
        personslist.append(pers.complete_name)
        pidList.append(str(pers.id))

    if request.method == "POST":
        id = updateFaces(request.form, pidList)
    else:
        id = request.args.get("id", None)

    if id is None:
        return

    photo = Photo.objects(id=id).first()
    b64 = base64.b64encode(photo.photo.read())
    b64_photo = b64.decode("UTF-8")

    b64_faces = []
    names_slug = []
    for face in photo.faces:
        if not face.person is None:
            person = face.person
            pid = str(person.id)
            auto_recog = False
            if face.manually_tagged:
                score = "Tag manuel"
            else:
                score = "Score : %.3f" % face.recognition_score
        else:
            person, score = face.recognize()
            face.person = person
            face.recognition_score = score
            face.save()

            if person is None:
                pid = ""
                score = "Aucune personne reconnue"
            else:
                pid = str(person.id)
                score = "Score : %.3f" % score
            auto_recog = True

        names_slug.append(
            (
                pid,
                str(face.id),
                # not face.recognition_score is None and not face.manually_tagged,
                auto_recog,
                score,
            )
        )
        img = face.getImage()
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        b64 = base64.b64encode(buf.getbuffer())
        b64_faces.append(b64.decode("UTF-8"))

    if photo.place_taken is None:
        lat = ""
        lon = ""
        alt = ""
    else:
        lat = photo.place_taken.latitude
        lon = photo.place_taken.longitude
        alt = photo.place_taken.altitude

    return render_template(
        "photo.html",
        photo_id=id,
        photo=b64_photo,
        faces=b64_faces,
        names_slug=names_slug,
        personslist=list(zip(pidList, personslist)),
        photo_lat=lat,
        photo_lon=lon,
        photo_alt=alt,
        photo_date=datetime.strftime(photo.date_taken, date_fmt),
    )
