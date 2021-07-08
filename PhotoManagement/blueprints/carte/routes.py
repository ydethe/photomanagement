import time

from flask import (
    render_template,
    request,
    flash,
    redirect,
    url_for,
    Markup,
)
from flask_login import login_required

from ... import logger
from ...config import Config
from . import carte_bp, createMap


@carte_bp.route("/get_map")
@login_required
def get_map():
    folium_map = createMap()
    return folium_map._repr_html_()


@carte_bp.route("/")
@login_required
def carte():
    return render_template("carte.html")
