import numpy as np
from scipy import linalg as lin
from scipy.spatial.distance import mahalanobis
from scipy.stats import chi, chi2

from .db import Person
from . import am, logger
from .config import Config


class CandidatesList(object):
    def __init__(self):
        self._db = {}
        for p in Person.objects:
            nfaces = len(p.faces)
            m = np.empty((128, nfaces), dtype=np.float64)
            for k, f in enumerate(p.faces):
                m[:, k] = f.blob

            avg = np.mean(m, axis=1, dtype=np.float64)
            print(np.cov(m[10, :] - avg[10]))
            cov = np.cov(m, dtype=np.float64)
            print(cov[10, 10])
            S = np.linalg.cholesky(lin.inv(cov))

            self._db[p.id] = (avg, S)
            break
        logger.info("Built recog engine database done")

    def testBlob(self, tested_blob: np.array):
        # th=chi2.ppf(df=128, q=Config.RECOGNITION_THRESHOLD)
        pmax = -1
        for pid in self._db.keys():
            avg, S = self._db[pid]

            Sd = S @ (tested_blob - avg)
            d2 = Sd @ Sd

            proba = chi2.cdf(df=128, x=d2)
            print(d2, proba)

            if proba > pmax:
                pmax = proba
                matching_pers = pid

        return matching_pers, pmax
