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


def buildPersonsList():
    res = []
    for p in Person.objects():
        nom = p.complete_name
        face = p.faces[0]
        img = face.getB64Image()
        b64img = img.decode("UTF-8")

        res.append((p.id, nom, b64img))

    return res
