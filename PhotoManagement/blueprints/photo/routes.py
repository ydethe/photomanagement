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


# 2020-04-08 21:32:50
date_fmt = "%Y/%m/%d %H:%M:%S"


def buildDisplayList(year: int, month: int, day: int) -> list:
    if year is None or year == "":
        q = Photo.objects.order_by("date_taken")
        disp_list = [photo.date_taken.year for photo in q]
    elif month is None or month == "":
        dt_inf = datetime(year=year, month=1, day=1, hour=0, minute=0, second=0)
        dt_sup = datetime(year=year + 1, month=1, day=1, hour=0, minute=0, second=0)
        q = (
            Photo.objects.filter(date_taken__gte=dt_inf)
            .filter(date_taken__lt=dt_sup)
            .order_by("date_taken")
        )
        disp_list = [photo.date_taken.month for photo in q]
    elif day is None or day == "":
        dt_inf = datetime(year=year, month=month, day=1, hour=0, minute=0, second=0)
        dt_sup = datetime(year=year, month=month + 1, day=1, hour=0, minute=0, second=0)
        q = (
            Photo.objects.filter(date_taken__gte=dt_inf)
            .filter(date_taken__lt=dt_sup)
            .order_by("date_taken")
        )
        disp_list = [photo.date_taken.day for photo in q]
    elif not day is None and day != "":
        dt_inf = datetime(year=year, month=month, day=day, hour=0, minute=0, second=0)
        dt_sup = datetime(
            year=year, month=month, day=day + 1, hour=0, minute=0, second=0
        )
        q = (
            Photo.objects.filter(date_taken__gte=dt_inf)
            .filter(date_taken__lt=dt_sup)
            .order_by("date_taken")
        )
        disp_list = [photo.id for photo in q]

    # Remove duplicates
    disp_list = list(dict.fromkeys(disp_list))

    return disp_list


def updateFaces(data: dict) -> str:
    # ImmutableMultiDict([('photo_id', '60d4db7bd9685a94e51b3d25'), ('input-yann-blaudin-de-the', 'alix-de-chanterac'), ('input-ines-blaudin-de-the', 'ines-blaudin-de-the')])
    # print(data)
    # photo_id = data.get("photo_id", None)

    for k in data.keys():
        v = data[k]
        if k == "photo_lat":
            continue
        elif k == "photo_lon":
            continue
        elif k == "photo_alt":
            continue
        elif k == "photo_date":
            date_taken = datetime.strptime(v, date_fmt)
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


@photo_bp.route("/")
def photo_defaults():
    return photo(year="", month="", day="", photo_id="")


@photo_bp.route(
    "/<int:year>",
    defaults={"month": "", "day": "", "photo_id": "", "previous_photo_id": ""},
)
@photo_bp.route(
    "/<int:year>/<int:month>",
    defaults={"day": "", "photo_id": "", "previous_photo_id": ""},
)
@photo_bp.route(
    "/<int:year>/<int:month>/<int:day>",
    defaults={"photo_id": "", "previous_photo_id": ""},
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
