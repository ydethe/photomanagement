import os

from PhotoManagement.db import Face, Photo, Person
from PhotoManagement.Image import read_metadata


root0 = "tests/Visages"
for root, dirs, files in os.walk(root0):
    if root == ".":
        continue

    pers = Person()
    pers.save()

    for f in files:
        pass
