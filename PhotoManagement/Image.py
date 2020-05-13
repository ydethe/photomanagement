import datetime
import os
import time

from PIL import Image
from PIL.ExifTags import TAGS


def read_capture_date_and_time(pth):
    im = Image.open(pth)
    exif_data = im._getexif()
    im.close()
    
    labeled = {}
    for (key, val) in exif_data.items():
        labeled[TAGS.get(key)] = val

    # '2020:04:02 12:58:12'
    date_time_str = labeled['DateTimeOriginal']
    date_time_obj = datetime.datetime.strptime(date_time_str, '%Y:%m:%d %H:%M:%S')

    return date_time_obj

def modTime(pth, dt):
    modTime = time.mktime(dt.timetuple())
    os.utime(pth, (modTime, modTime))
