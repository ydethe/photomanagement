import base64

from flask import Flask
from flask import Blueprint


recherche_bp = Blueprint("recherche", __name__, template_folder="templates")

from .routes import *
