# __init__.py
from flask.templating import render_template
from pkg_resources import get_distribution
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import os

import sentry_sdk
from flask import Flask, redirect, url_for
from flask_mongoengine import MongoEngine
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import *
from sentry_sdk.integrations.flask import FlaskIntegration

from .LogFormatter import LogFormatter
from .config import Config
from .AirtableManager import AirtableManager

__version__ = get_distribution(__name__).version

__author__ = "Y. BLAUDIN DE THE"
__email__ = "ydethe@gmail.com"


# création de l'objet logger qui va nous servir à écrire dans les logs
logger = logging.getLogger("photomgt_logger")

# on met le niveau du logger à DEBUG, comme ça il écrit tout
logger.setLevel(logging.DEBUG)
# logger.setLevel(logging.INFO)

# création d'un formateur qui va ajouter le temps, le niveau
# de chaque message quand on écrira un message dans le log
formatter = LogFormatter()
# création d'un handler qui va rediriger chaque écriture de log
# sur la console
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

file_handler = RotatingFileHandler(
    "photomgt.log",
    mode="a",
    maxBytes=1000000,
    backupCount=1,
    encoding="utf-8",
    delay=True,
)
file_handler.setFormatter(formatter)

logger.handlers = []
logger.addHandler(stream_handler)
logger.addHandler(file_handler)

sentry_sdk.init(
    dsn="https://2c3d694b175245dc9dc0a7e543786bb9@o913274.ingest.sentry.io/5851004",
    integrations=[FlaskIntegration()],
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
)

app = Flask(__name__, instance_relative_config=True)
app.config.from_object(Config)
bootstrap = Bootstrap(app)
app.logger.addHandler(file_handler)
db = MongoEngine(app)

am = AirtableManager()


@app.route("/")
def index():
    return redirect(url_for("photo.photo_defaults"))


from .blueprints.carte import carte_bp

app.register_blueprint(carte_bp, url_prefix="/carte")

from .blueprints.photo import photo_bp

app.register_blueprint(photo_bp, url_prefix="/photo")

from .blueprints.recherche import recherche_bp

app.register_blueprint(recherche_bp, url_prefix="/recherche")

topbar = Navbar(
    "johncloud.fr",
    View("Carte", "carte.carte"),
    View("Photos", "photo.photo_defaults"),
    View("Personnes", "photo.personnes"),
    View("Recherche", "recherche.recherche"),
)

# registers the "top" menubar
nav = Nav()
nav.register_element("top", topbar)

nav.init_app(app)
