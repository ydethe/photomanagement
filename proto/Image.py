from datetime import datetime
import os
import time
from datetime import datetime

from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata


def get_decimal_coordinates(info):
    for key in ["Latitude", "Longitude"]:
        if "GPS" + key in info and "GPS" + key + "Ref" in info:
            e = info["GPS" + key]
            ref = info["GPS" + key + "Ref"]

            s = 0
            mul = [1, 60, 3600]
            for k, m in enumerate(mul):
                s += float(e[0]) / m

            info[key] = s * (-1 if ref in ["S", "W"] else 1)

    if "Latitude" in info and "Longitude" in info:
        return [info["Latitude"], info["Longitude"]]


def read_metadata(pth):
    im = Image.open(pth)
    exif_data = im._getexif()
    _, fn = os.path.split(pth)
    bn, _ = os.path.splitext(fn)

    # with open("md/metadata_%s.txt" % fn, "w") as f:
    #     f.write("%s\n" % pth)
    #     f.write(str(exif_data))
    # im.close()

    if exif_data is None or not "DateTimeOriginal" in exif_data.keys():
        # bn="Photo 20-03-13 17-53-52 0558"
        dt = datetime.strptime(bn, "Photo %y-%m-%d %H-%M-%S %f")
        return {"DateTimeOriginal": dt}

    lkeys = list(exif_data.keys())
    for key in lkeys:
        name = TAGS.get(key, key)
        exif_data[name] = exif_data.pop(key)

    if "GPSInfo" in exif_data:
        lkeys = list(exif_data["GPSInfo"].keys())
        for key in lkeys:
            name = GPSTAGS.get(key, key)
            exif_data["GPSInfo"][name] = exif_data["GPSInfo"].pop(key)

        lat, lon = get_decimal_coordinates(exif_data["GPSInfo"])
        exif_data["GPSInfo"]["Latitude"] = lat
        exif_data["GPSInfo"]["Longitude"] = lon

    # f = open("log_pil.txt", "w")
    # f.write(str(exif_data))
    # f.close()

    # '2020:04:02 12:58:12'
    date_time_str = exif_data["DateTimeOriginal"]
    exif_data["DateTimeOriginal"] = datetime.strptime(
        date_time_str, "%Y:%m:%d %H:%M:%S"
    )

    return exif_data


if __name__ == "__main__":
    pth = "Mars2020/Photo 20-03-28 15-35-36 0667.jpg"
    read_metadata(pth)
