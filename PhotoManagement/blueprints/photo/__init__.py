import base64

from flask import Flask
from flask import Blueprint


photo_bp = Blueprint("photo", __name__, template_folder="templates")

from .routes import *
