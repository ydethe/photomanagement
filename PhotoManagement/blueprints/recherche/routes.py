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
from . import recherche_bp
from ...Photo import Photo
from ...Face import Face
from ...Person import Person
from ..photo.utils import buildPersonsList


@recherche_bp.route("/form")
def form():
    plist = buildPersonsList()
    return render_template("recherche.html", personslist=plist)


@recherche_bp.route("/resultats", methods=["POST"])
def resultats():
    date_fmt = "%d/%m/%Y %H:%M:%S"

    if request.method == "POST":
        q = Photo.objects()
        dateDebut = request.form.get("dateDebut", None)
        dateFin = request.form.get("dateFin", None)
        lpers = request.form.getlist("inputPersonne")
        if not dateDebut is None:
            dateDebut = datetime.strptime(dateDebut, date_fmt)
            q = q.filter(date_taken__gte=dateDebut)
        if not dateFin is None:
            dateFin = datetime.strptime(dateFin, date_fmt)
            q = q.filter(date_taken__lt=dateFin)

    plist = buildPersonsList()
    return render_template("recherche.html", personslist=plist)
