""" Usage:

    Start the flask server by running:

        $ python tests/test_map_flask.py

    And then head to http://127.0.0.1:5000/ in your browser to see the map displayed

"""
import base64

from flask import Flask
import folium
from folium import IFrame
from mongoengine import connect

from PhotoManagement.db import Address


def createMap():
    lat = []
    lon = []
    info = []
    lat_min = None
    lat_max = None
    lon_min = None
    lon_max = None
    for a in Address.objects():
        if len(a.photos) == 0:
            continue

        photo = a.photos[0]

        lat.append(a.latitude)
        lon.append(a.longitude)
        if lat_min is None or a.latitude < lat_min:
            lat_min = a.latitude
        if lat_max is None or a.latitude > lat_max:
            lat_max = a.latitude
        if lon_min is None or a.longitude < lon_min:
            lon_min = a.longitude
        if lon_max is None or a.longitude > lon_max:
            lon_max = a.longitude

        if not hasattr(photo, "miniature"):
            print("No miniature photo id=%s" % photo.id)
            continue

        mini = photo.miniature.read()
        encoded = base64.b64encode(mini)
        svg = """
        <object data="data:image/jpg;base64,{}" width="{}" height="{} type="image/svg+xml">
        </object>""".format
        width, height, fat_wh = 78, 78, 1.25
        iframe = IFrame(
            svg(encoded.decode("UTF-8"), width, height),
            width=width * fat_wh,
            height=height * fat_wh,
        )
        popup = folium.Popup(iframe, max_width=2650)
        info.append(popup)

    m = folium.Map(
        location=[lat_min / 2 + lat_max / 2, lon_min / 2 + lon_max / 2],
        tiles="Stamen Terrain",
    )

    for xlat, xlon, xinfo in zip(lat, lon, info):
        folium.Marker([xlat, xlon], popup=xinfo).add_to(m)

    m.fit_bounds([[lat_min, lon_min], [lat_max, lon_max]])

    return m


connect("photo_mgt")

app = Flask(__name__)


@app.route("/")
def index():
    folium_map = createMap()
    return folium_map._repr_html_()


if __name__ == "__main__":
    app.run(debug=True)
