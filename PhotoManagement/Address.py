# Address.py
import io
import os
from enum import Enum, unique
from typing import Tuple

from mongoengine import (
    Document,
    IntField,
    FloatField,
    StringField,
    ListField,
    ReferenceField,
    BooleanField,
    ImageField,
    DateTimeField,
    DictField,
    EmailField,
    EnumField,
    URLField,
)
from tqdm import tqdm
from mongoengine import signals
from PIL import Image, ImageDraw
from pkg_resources import require
import what3words
import geocoder

from . import logger, db


def get_decimal_coordinates(info: dict) -> Tuple[float]:
    for key in ["Latitude", "Longitude"]:
        if "GPS" + key in info and "GPS" + key + "Ref" in info:
            e = info["GPS" + key]
            ref = info["GPS" + key + "Ref"]

            s = 0
            mul = [1, 60, 3600]
            for k, m in enumerate(mul):
                s += float(e[k]) / m

            info[key] = s * (-1 if ref in ["S", "W"] else 1)

    if "Latitude" in info and "Longitude" in info:
        return [info["Latitude"], info["Longitude"]]
    else:
        return None, None


def getAddress(lat: float, lon: float, alt: float) -> dict:
    """

    >>> getAddress(43.60467117912294,1.4415632156260192,0)
    {'city': 'Toulouse',
     'country': 'France',
     'country_code': 'fr',
     'county': 'Haute-Garonne',
     'municipality': 'Toulouse',
     'neighbourhood': 'Place Occitane',
     'postcode': '31000',
     'road': 'Rue Jean-Antoine Romiguières',
     'shop': 'Jean Claude Aubry Romiguières',
     'state': 'Occitanie',
     'suburb': 'Toulouse Centre'}

    """
    w3wgc = what3words.Geocoder("642RI3LY")
    res = w3wgc.convert_to_3wa(what3words.Coordinates(lat, lon))
    q = Address.objects(w3w=res["words"])
    if q.count() > 0:
        return q.first()

    g = geocoder.osm([lat, lon], method="reverse")
    dat = g.geojson["features"][0]["properties"]["raw"]["address"]

    if "city" in dat.keys():
        ville = dat["city"]
    elif "village" in dat.keys():
        ville = dat["village"]
    elif "town" in dat.keys():
        ville = dat["town"]

    try:
        addr = dict(
            ville=ville,
            pays=dat["country"],
            rue=dat.get("road", ""),
            numero=int(dat.get("house_number", "0")),
            code_postal=dat["postcode"],
            latitude=lat,
            longitude=lon,
            altitude=alt,
            w3w=res["words"],
        )
    except Exception as e:
        print(dat)
        exit(1)

    return addr


class Address(db.Document):
    ville = StringField()
    pays = StringField()
    rue = StringField()
    numero = IntField()
    code_postal = StringField()
    latitude = FloatField()
    longitude = FloatField()
    altitude = FloatField()
    photos = ListField(ReferenceField("Photo"))
    w3w = StringField(unique=True)
