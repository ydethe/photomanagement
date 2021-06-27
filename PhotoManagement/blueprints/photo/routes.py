from PhotoManagement.Person import Person
import time
import base64
import io

from slugify import slugify
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
    if request.method == "POST":
        logger.debug("Logging form")
        print(request.form)
        id = "60d4db7bd9685a94e51b3d25"
    else:
        id = request.args.get("id", None)

    if id is None:
        return

    photo = Photo.objects(id=id).first()
    b64 = base64.b64encode(photo.photo.read())
    b64_photo = b64.decode("UTF-8")

    am = AirtableManager()

    personslist = []
    slugsList = []
    for pers in Person.objects():
        rec = pers.getAirtableInformation()
        personslist.append(rec["Nom complet"])
        slugsList.append(slugify(rec["Nom complet"]))

    faces = photo.faces
    b64_faces = []
    names_slug = []
    for face in faces:
        if not face.person is None:
            person = face.person
            aid = person.airtable_id
            if not aid.startswith("rec"):
                nom = aid
            else:
                rec = am.get_rec_by_id("pers_table", aid)
                nom = rec["fields"]["Nom complet"]
        else:
            nom = "[unknown]"

        names_slug.append(slugify(nom))
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
        personslist=list(zip(slugsList, personslist)),
    )
