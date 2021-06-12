import time

from flask import (
    render_template,
    request,
    flash,
    redirect,
    url_for,
    Markup,
)

from ... import logger
from ...config import Config
from . import carte_bp, createMap


@carte_bp.route("/get_map")
def get_map():
    folium_map = createMap()
    return folium_map._repr_html_()


@carte_bp.route("/")
def carte():
    return render_template("carte.html")
