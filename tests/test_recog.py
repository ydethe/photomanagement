from PhotoManagement.Face import Face


q = Face.objects(manually_tagged=False)
for face in q:
    pers, score = face.recognize()
    rec = pers.getAirtableInformation()
    face.show("%s, %.4f" % (rec["Nom complet"], score))
