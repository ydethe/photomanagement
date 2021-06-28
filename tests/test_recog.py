from tqdm import tqdm

from PhotoManagement.Face import Face
from PhotoManagement.Person import Person
from PhotoManagement import logger

# Camille : recN3JQkfbFwI8MO2
# Ines : rec4zSxHj80wVCsqO
# Louis : recxiwVa0DwKSdEmQ
# Mam : recrdwc11XMQ6GpMQ
# Marine : recxL905NCWIgK1lA
# Pacha : recH8DRAG8NvVHyWp
# Roch : recqtqQ7xLOMbyFER
# Yann : rec7kGIwPvyF88c9B
# Alix : recveqTy7lwXH6TOZ
# Quitterie : recXpwgB0ESvY6W2A
# Dad : recKNXFvWuxvDfqL0
# Mere : recglWKYemBIP9BUn
# Tiphaine : reccgVoUyKC2YtKVv
# Rémi : recuokZlLua8RzbT6

qset = Face.objects
for face in tqdm(
    qset.filter(manually_tagged=False).filter(recognition_score__exists=False)
):
    if face.size < 40:
        logger.info("Face size %i. Skipping." % face.size)
        face.delete()
        continue

    logger.debug("Photo id %s" % face.photo.id)

    logger.debug("Face size %i" % face.size)
    pers, score = face.recognize()
    rec = pers.complete_name

    # face.show("%s\n%.4f" % (rec["Nom complet"], score))
    Face.showPhotoForFace(hash=face.hash)
    chx = input("OK?")

    if chx == "" or chx.lower() == "y" or chx.lower() == "yes":
        face.person = pers
        face.recognition_score = score
        face.save()
        pers.faces.append(face)
        pers.save()
        logger.info("Recorded %s" % rec["Nom complet"])
    elif chx.lower() == "supp":
        face.delete()
        logger.info("Face deleted")
    elif chx.startswith("rec") or chx.lower() == "roch":
        q = Person.objects(airtable_id=chx)
        while q.count() != 1:
            logger.error("Unknown airtable rec %s" % chx)
            chx = input("id?")
            q = Person.objects(airtable_id=chx)
        pers = q.first()
        rec = pers.complete_name
        logger.info("Manually tagged %s" % rec["Nom complet"])
        face.person = pers
        face.manually_tagged = True
        face.save()
        pers.faces.append(face)
        pers.save()
