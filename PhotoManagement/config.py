import os

basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig(object):
    FLASK_ADMIN_SWATCH = "cerulean"
    MONGODB_DB = "photo_mgt"
    MONGODB_HOST = "localhost"
    MONGODB_PORT = 27017
    MONGODB_USERNAME = "ydethe"
    MONGODB_PASSWORD = "Te1gpqS"

    AIRTABLE_KEY = "keyngIzDMBmUDJE4Z"
    AIRTABLE_TABLE = "appXvX7qHnPtnThgH"
    AIRTABLE_PERSON = "Personne"


Config = BaseConfig
