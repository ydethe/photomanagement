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
    t0 = time.time()

    am = AirtableManager()

    personslist = ["Inconnu"]
    pidList = [""]
    for pers in Person.objects():
        personslist.append(pers.complete_name)
        pidList.append(str(pers.id))
    logger.debug("%.3f" % (time.time() - t0))

    if request.method == "POST":
        # ImmutableMultiDict([('photo_id', '60d4db7bd9685a94e51b3d25'), ('input-yann-blaudin-de-the', 'alix-de-chanterac'), ('input-ines-blaudin-de-the', 'ines-blaudin-de-the')])
        # print(request.form)
        # print(pidList)
        id = request.form.get("photo_id", None)
        for k in request.form.keys():
            v = request.form[k]
            if k == "photo_id":
                photo = Photo.objects(id=v).first()
                nphoto = photo.next()
                id = nphoto.id
                continue

            face_id = k[6:]
            ipers = pidList.index(v)
            pers_id = pidList[ipers]
            logger.debug("%s, %s" % (face_id, pers_id))
            qf = Face.objects(id=face_id)
            qp = Person.objects(id=pers_id)
            if qp.count() != 1:
                logger.error("Person id unknown %s" % pers_id)
            if qf.count() != 1:
                logger.error("Face id unknown %s" % face_id)
            if qp.count() == 1 and qf.count() == 1:
                pers = qp.first()
                face = qf.first()
                face.affectToPersonAndSaveAll(pers)

    else:
        id = request.args.get("id", None)

    if id is None:
        return

    photo = Photo.objects(id=id).first()
    b64 = base64.b64encode(photo.photo.read())
    b64_photo = b64.decode("UTF-8")
    logger.debug("%.3f" % (time.time() - t0))

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

        names_slug.append((pid, face.id))
        img = face.getImage()
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        b64 = base64.b64encode(buf.getbuffer())
        b64_faces.append(b64.decode("UTF-8"))
    logger.debug("%.3f" % (time.time() - t0))

    return render_template(
        "photo.html",
        photo_id=id,
        photo=b64_photo,
        faces=b64_faces,
        names_slug=names_slug,
        personslist=list(zip(pidList, personslist)),
    )
