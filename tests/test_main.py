import os
import unittest
import datetime
from shutil import copyfile

from PhotoManagement.Image import read_capture_date_and_time, setModTime, getModTime


class TestImage (unittest.TestCase):
    def setUp(self):
        pth1 = os.path.join(os.getcwd(),"tests","children.jpg")
        pth2 = os.path.join(os.getcwd(),"tests","test.jpg")
        copyfile(pth1, pth2)

    def test_exif(self):
        pth = os.path.join(os.getcwd(),"tests","test.jpg")
        date = read_capture_date_and_time(pth)

        self.assertEqual(date, datetime.datetime(2020, 4, 2, 12, 58, 23))
        
    def test_mod_time(self):
        pth = os.path.join(os.getcwd(),"tests","test.jpg")
        date2 = datetime.datetime(2021, 4, 2, 12, 58, 12)
        setModTime(pth, date2)
        date = getModTime(pth)
        self.assertEqual(date, date2)

        