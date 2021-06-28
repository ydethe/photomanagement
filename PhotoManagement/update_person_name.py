from tqdm import tqdm

from . import logger
from .Person import Person


def update_person_name():
    for pers in tqdm(Person.objects):
        rec = pers.getAirtableInformation()
        pers.complete_name = rec["Nom complet"]
        pers.save()


if __name__ == "__main__":
    update_person_name()
