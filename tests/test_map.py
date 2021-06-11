import matplotlib.pyplot as plt

# Import, and set to log to the console.  (See the console which is running
# Jupyter notebook for logging about HTTP requests.)
import tilemapbase
from mongoengine import connect

from PhotoManagement.db import Address


tilemapbase.start_logging()

# Don't need if you have run before; DB file will already exist.
tilemapbase.init(create=True)

# Use open street map
t = tilemapbase.tiles.build_OSM()

connect("photo_mgt")

lat = []
lon = []
lat_min = None
lat_max = None
lon_min = None
lon_max = None
for a in Address.objects():
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

degree_range = 0.003
extent = tilemapbase.Extent.from_lonlat(
    lon_min - degree_range,
    lon_max + degree_range,
    lat_min - degree_range,
    lat_max + degree_range,
)
extent = extent.to_aspect(1.0)

# On my desktop, DPI gets scaled by 0.75
fig, ax = plt.subplots(figsize=(8, 8), dpi=100)
ax.xaxis.set_visible(False)
ax.yaxis.set_visible(False)

plotter = tilemapbase.Plotter(extent, t, width=600)
plotter.plot(ax, t)

xy = [tilemapbase.project(xlon, xlat) for (xlon, xlat) in zip(lon, lat)]
x, y = zip(*xy)
ax.scatter(x, y, marker=".", color="black", linewidth=20)

plt.show()
