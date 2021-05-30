import argparse

from PhotoManagement.Image import read_capture_date_and_time


def main():
    print("OK")
    import sys

    pth = sys.argv[1]
    exif_data = read_capture_date_and_time(pth)
    print(exif_data)
