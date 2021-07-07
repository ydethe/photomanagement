from mongoengine.connection import disconnect
from pkg_resources import require
from datetime import datetime

from bson import ObjectId
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
from . import recherche_bp
from ...Photo import Photo
from ...Face import Face
from ...Person import Person
from ..photo.utils import buildPersonsList, str_to_datetime


@recherche_bp.route("/form")
def form():
    plist = buildPersonsList()
    return render_template("recherche.html", personslist=plist)


@recherche_bp.route("/resultats", methods=["POST"])
def resultats():
    q = Photo.objects()
    dateDebut = str_to_datetime(request.form.get("dateDebut", None))
    dateFin = str_to_datetime(request.form.get("dateFin", None))
    lpers = request.form.getlist("inputPersonne")
    if not dateDebut is None:
        q = q.filter(date_taken__gte=dateDebut)
    if not dateFin is None:
        q = q.filter(date_taken__lt=dateFin)
    q_pers = Person.objects(id__in=lpers)
    pipeline = [
        {
            "$lookup": {
                "from": "face",
                "localField": "faces",
                "foreignField": "_id",
                "as": "faces_info",
            }
        },
        {
            "$match": {
                "$and": [
                    {"faces_info": {"$elemMatch": {"person": p.id}}} for p in q_pers
                ]
            }
        },
    ]

    # Verif que les photos retournées conviennent
    # q_photos = Photo.objects().aggregate(pipeline)
    # for photo in q_photos:
    #     photo_id=photo['_id']
    #     for face in Photo.objects(id=photo_id).get().faces:
    #         if face.person is None:
    #             continue

    #         print(str(face.person.id), lpers)
    #         # if str(face.person.id) in lpers:
    #         #     return
    #     print()

    q_photos = Photo.objects().aggregate(pipeline)
    l_photo = []
    for photo in q_photos:
        photo_id = photo["_id"]
        photo = Photo.objects(id=photo_id).get()
        img = photo.getB64Miniature()
        b64img = img.decode("UTF-8")
        y = photo.date_taken.year
        m = photo.date_taken.month
        d = photo.date_taken.day
        url = "/photo/%s/%s/%s/%s" % (y, m, d, photo_id)
        l_photo.append((url, b64img))

    return render_template("resultats.html", photosList=l_photo)
