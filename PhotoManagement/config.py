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

    W3W_KEY = "642RI3LY"

    RECOGNITION_THRESHOLD = 0.90

    SECRET_KEY = "C2HWGVorTyyZGfNTBsrYQg8EcMrdTimkZfAb"


Config = BaseConfig
