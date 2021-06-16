import numpy as np
from scipy import linalg as lin
from scipy.spatial.distance import mahalanobis
from scipy.stats import chi, chi2

from .db import Person
from . import am, logger
from .config import Config


class CandidatesList(object):
    def __init__(self):
        # Dimension
        nd = 128

        self._db = {}
        for p in Person.objects:
            nfaces = len(p.faces)
            m = np.empty((128, nfaces), dtype=np.float64)
            for k, f in enumerate(p.faces):
                m[:, k] = f.blob

            avg = np.mean(m, axis=1, dtype=np.float64)
            # Pas la covariance complete car nd > nfaces ==> non symetrique def. positive
            std = [np.std(m[k, :], dtype=np.float64) for k in range(nd)]

            self._db[p.id] = (avg, std)

        logger.info("Built recog engine database")

    def testBlob(self, tested_blob: np.array):
        dmin = None
        for pid in self._db.keys():
            avg, std = self._db[pid]

            delta = (tested_blob - avg) / std
            d2 = delta @ delta

            p = Person.objects(id=pid).first()
            aid = p.airtable_id
            if aid.startswith("rec"):
                rec = am.get_rec_by_id("pers_table", aid)
                test_name = rec["fields"]["Nom complet"]
            else:
                test_name = aid

            logger.debug(" Testing %s -> d = %.3f" % (test_name, np.sqrt(d2)))

            if dmin is None or d2 < dmin:
                dmin = d2
                matching_pers = pid

        return matching_pers, np.sqrt(d2)


if __name__ == "__main__":
    cl = CandidatesList()
