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


@recherche_bp.route("/", methods=["GET", "POST"])
def recherche():
    if request.method == "POST":
        print(request.form)

    plist = buildPersonsList()
    return render_template("recherche.html", personslist=plist)
