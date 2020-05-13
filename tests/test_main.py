import os
import unittest

from PhotoManagement.Image import read_capture_date_and_time


class TestImage (unittest.TestCase):
    def test_exif(self):
        pth = os.path.join(os.getcwd(),"tests","fleur.jpg")
        exif_data = read_capture_date_and_time(pth)
        dat = str(exif_data)
        f = open('log.txt','w')
        f.write(dat)
        f.close()
        