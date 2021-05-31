from datetime import datetime
import os
import time

from PIL import Image
from PIL.ExifTags import TAGS
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata


def _jpeg_cdt(pth):
    im = Image.open(pth)
    exif_data = im._getexif()
    im.close()

    labeled = {}
    for (key, val) in exif_data.items():
        labeled[TAGS.get(key)] = val

    # '2020:04:02 12:58:12'
    date_time_str = labeled["DateTimeOriginal"]
    date_time_obj = datetime.strptime(date_time_str, "%Y:%m:%d %H:%M:%S")

    return date_time_obj


def _png_cdt(pth):
    im = Image.open(pth)
    exif_data = im._getexif()
    im.close()

    labeled = {}
    for (key, val) in exif_data.items():
        labeled[TAGS.get(key)] = val

    f = open("log_pil.txt", "w")
    f.write(str(labeled))
    f.close()

    parser = createParser(pth)
    metadata = extractMetadata(parser)
    d = metadata.exportDictionary()

    # f = open("log_hachoir.txt", "w")
    # f.write(str(d))
    # f.close()

    # '2020:04:02 12:58:12'
    date_time_str = labeled["DateTimeOriginal"]
    date_time_obj = datetime.strptime(date_time_str, "%Y:%m:%d %H:%M:%S")

    return date_time_obj


def read_capture_date_and_time(pth:str)->datetime:
    _, ext = os.path.splitext(pth.lower())
    if ext == ".jpg" or ext == ".jpeg" or ext == ".tiff":
        dt = _jpeg_cdt(pth)
    elif ext == ".png" or ext == ".heic" or ext == ".gif":
        dt = _png_cdt(pth)
    else:
        print("[ERREUR]%s : extension inconnu" % pth)

    return dt


def setModTime(pth, dt):
    modTime = time.mktime(dt.timetuple())
    os.utime(pth, (modTime, modTime))


def getModTime(pth):
    mt = os.path.getmtime(pth)
    dt = datetime.datetime.fromtimestamp(mt)
    return dt
