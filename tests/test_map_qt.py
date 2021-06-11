import io
import sys
import base64

import folium
from folium import IFrame
from mongoengine import connect
from PyQt5 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets

from PhotoManagement.db import Address


connect("photo_mgt")


class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.initWindow()

    def initWindow(self):
        self.setWindowTitle(self.tr("MAP PROJECT"))
        self.setFixedSize(1500, 800)
        self.buttonUI()

    def buttonUI(self):
        shortPathButton = QtWidgets.QPushButton(self.tr("Find shortest path"))
        button2 = QtWidgets.QPushButton(self.tr("Another path"))
        button3 = QtWidgets.QPushButton(self.tr("Another path"))

        shortPathButton.setFixedSize(120, 50)
        button2.setFixedSize(120, 50)
        button3.setFixedSize(120, 50)

        self.view = QtWebEngineWidgets.QWebEngineView()
        self.view.setContentsMargins(50, 50, 50, 50)

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        lay = QtWidgets.QHBoxLayout(central_widget)

        button_container = QtWidgets.QWidget()
        vlay = QtWidgets.QVBoxLayout(button_container)
        vlay.setSpacing(20)
        vlay.addStretch()
        vlay.addWidget(shortPathButton)
        vlay.addWidget(button2)
        vlay.addWidget(button3)
        vlay.addStretch()
        lay.addWidget(button_container)
        lay.addWidget(self.view, stretch=1)

        m = self.createMap()

        data = io.BytesIO()
        m.save(data, close_file=False)
        self.view.setHtml(data.getvalue().decode())

    def createMap(self):
        lat = []
        lon = []
        info = []
        lat_min = None
        lat_max = None
        lon_min = None
        lon_max = None
        for a in Address.objects():
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

            encoded = base64.b64encode(photo.miniature.read())
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
            zoom_start=12,
            tiles="Stamen Terrain",
        )

        for xlat, xlon, xinfo in zip(lat, lon, info):
            folium.Marker([xlat, xlon], popup=xinfo).add_to(m)

        return m


if __name__ == "__main__":
    App = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(App.exec())
