from mongoengine.connection import disconnect
from pkg_resources import require
from datetime import datetime

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
from ...Person import Person
from .utils import buildDisplayList, updateFaces, buildPersonsList, date_fmt


@photo_bp.route("/personnes")
def personnes():
    plist = buildPersonsList()
    return render_template("personnes.html", plist=plist)


@photo_bp.route("/")
def photo_defaults():
    return photo(year="", month="", day="", photo_id="")


@photo_bp.route(
    "/<int:year>", defaults={"month": "", "day": "", "photo_id": ""},
)
@photo_bp.route(
    "/<int:year>/<int:month>", defaults={"day": "", "photo_id": ""},
)
@photo_bp.route(
    "/<int:year>/<int:month>/<int:day>", defaults={"photo_id": ""},
)
@photo_bp.route("/<int:year>/<int:month>/<int:day>/<photo_id>", methods=["POST", "GET"])
def photo(year, month, day, photo_id):
    # logger.debug("%s,%s,%s,%s"%(type(year),month,day,photo_id))
    if year == "":
        disp_list = buildDisplayList(year, month, day)
        return render_template("list_all.html", disp_list=disp_list)
    elif month == "":
        disp_list = buildDisplayList(year, month, day)
        l_month_names = [
            datetime.strftime(datetime(year=1986, month=m, day=20), "%B")
            for m in disp_list
        ]
        return render_template(
            "list_year.html", year=year, disp_list=zip(disp_list, l_month_names)
        )
    elif day == "":
        disp_list = buildDisplayList(year, month, day)
        month_name = datetime.strftime(datetime(year=1986, month=month, day=20), "%B")
        return render_template(
            "list_month.html",
            year=year,
            month=month,
            month_name=month_name,
            disp_list=disp_list,
        )
    elif photo_id == "":
        disp_list = buildDisplayList(year, month, day)
        return render_template(
            "list_day.html", year=year, month=month, day=day, disp_list=disp_list
        )

    personslist = ["Inconnu"]
    pidList = [""]
    for pers in Person.objects():
        personslist.append(pers.complete_name)
        pidList.append(str(pers.id))

    if request.method == "POST":
        # print(request.form)
        updateFaces(request.form)

    # Find next photo
    photo = Photo.objects(id=photo_id).first()
    photo_year, photo_month, photo_month_name, photo_day, _ = photo.date_elements
    nphoto = (
        Photo.objects(date_taken__gt=photo.date_taken).order_by("date_taken").first()
    )
    (
        next_photo_year,
        next_photo_month,
        next_photo_month_name,
        next_photo_day,
        next_photo_id,
    ) = nphoto.date_elements

    b64 = base64.b64encode(photo.photo.read())
    b64_photo = b64.decode("UTF-8")

    b64_faces = []
    names_slug = []
    for face in photo.faces:
        if not face.person is None:
            person = face.person
            pid = str(person.id)
            if face.manually_tagged or not face.recognition_score:
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

        auto_recog = not face.manually_tagged

        names_slug.append(
            (
                pid,
                str(face.id),
                # not face.recognition_score is None and not face.manually_tagged,
                auto_recog,
                score,
            )
        )
        img = face.getB64Image()
        b64_faces.append(img.decode("UTF-8"))

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
        photo_id=photo_id,
        photo_year=photo_year,
        photo_month=photo_month,
        photo_month_name=photo_month_name,
        photo_day=photo_day,
        next_photo_id=next_photo_id,
        next_photo_year=next_photo_year,
        next_photo_month=next_photo_month,
        next_photo_day=next_photo_day,
        photo=b64_photo,
        faces=b64_faces,
        names_slug=names_slug,
        personslist=list(zip(pidList, personslist)),
        photo_lat=lat,
        photo_lon=lon,
        photo_alt=alt,
        photo_date=datetime.strftime(photo.date_taken, date_fmt),
    )
