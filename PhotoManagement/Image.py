from PIL import Image


def read_capture_date_and_time(pth):
    im = Image.open(pth)
    exif_data = im._getexif()
    return exif_data
    