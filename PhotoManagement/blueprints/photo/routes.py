from pkg_resources import require
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


@photo_bp.route("/", methods=["POST", "GET"])
def photo():
    personslist = ["Inconnu"]
    pidList = [""]
    for pers in Person.objects():
        personslist.append(pers.complete_name)
        pidList.append(str(pers.id))

    if request.method == "POST":
        # ImmutableMultiDict([('photo_id', '60d4db7bd9685a94e51b3d25'), ('input-yann-blaudin-de-the', 'alix-de-chanterac'), ('input-ines-blaudin-de-the', 'ines-blaudin-de-the')])
        # print(request.form)
        # print(pidList)
        id = request.form.get("photo_id", None)
        for k in request.form.keys():
            v = request.form[k]
            if k == "photo_id":
                photo = Photo.objects(id=v).first()
                nphoto = Photo.objects(date_taken__gt=photo.date_taken).first()
                id = nphoto.id
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
                ipers = pidList.index(v)
                pers_id = pidList[ipers]
                qp = Person.objects(id=pers_id)
                if qp.count() != 1:
                    logger.error("Person id unknown %s" % pers_id)
                    pers = None
                else:
                    pers = qp.first()
                    logger.info(
                        "Face id %s affected to %s" % (face_id, pers.complete_name)
                    )
                    face.affectToPersonAndSaveAll(pers)

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
        else:
            person, score = face.recognize()
            if person is None:
                pid = ""
            else:
                pid = person.id

        names_slug.append(
            (
                pid,
                face.id,
                not face.recognition_score is None and not face.manually_tagged,
            )
        )
        img = face.getImage()
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        b64 = base64.b64encode(buf.getbuffer())
        b64_faces.append(b64.decode("UTF-8"))

    return render_template(
        "photo.html",
        photo_id=id,
        photo=b64_photo,
        faces=b64_faces,
        names_slug=names_slug,
        personslist=list(zip(pidList, personslist)),
    )
