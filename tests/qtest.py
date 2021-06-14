from collections import defaultdict
import numpy as np
from scipy import linalg as lin
from scipy.stats import chi, chi2
from matplotlib import pyplot as plt

# Dimension
nd = 128

# Number of faces per person
nf = 30

# Number of persons
npe = 3

data = []
embedding_list_test = []
expected = []
names = []
np.random.seed(1562337)
for kp in range(npe):
    loc = np.random.uniform(low=-1, high=1, size=nd) * 100
    # S=np.diag(np.random.uniform(low=-1, high=1, size=nd))
    S = np.triu(np.random.uniform(low=-1, high=1, size=(nd, nd)))

    # Training data
    for kf in range(kp * nf, (kp + 1) * nf):
        vec = S @ np.random.normal(size=nd) + loc
        data.append(vec)
        names.append("Person%i" % kp)

    # Test data
    vec = S @ np.random.normal(size=nd) * 0.9 + loc
    embedding_list_test.append(vec)
    expected.append("Person%i" % kp)

# ========================
# Classification
# ========================
db = {}
for kp in range(npe):
    name = "Person%i" % kp
    db[name] = []
    for k in range(len(names)):
        if names[k] == name:
            db[name].append(data[k])
    est_loc = np.empty(nd)
    est_std = np.empty(nd)
    for kd in range(nd):
        est_loc[kd] = np.mean([x[kd] for x in db[name]])
        est_std[kd] = np.std([x[kd] for x in db[name]])

    db[name] = (est_loc, est_std)

# ========================
# Prediction
# ========================
for kt, test in enumerate(embedding_list_test):
    print(kt)
    print("Name\tDistance\tProba.")
    for kp in range(npe):
        name = "Person%i" % kp
        est_loc, est_std = db[name]
        d2 = lin.norm((test - est_loc) / est_std) ** 2
        P = chi2.sf(x=d2, df=nd)
        print("%s\t%.2f\t\t%.1f%%" % (name, np.sqrt(d2), 100 * P))
    print()

# ========================
# Visualization
# ========================
fig = plt.figure()
axe = fig.add_subplot(111)
axe.grid(True)

v1 = 0
v2 = 1
kp = 2
dx = db["Person%i" % kp][1][0]
dy = db["Person%i" % kp][1][1]
axe.scatter(
    [v[v1] / dx for v in data[kp * nf : (kp + 1) * nf]],
    [v[v2] / dy for v in data[kp * nf : (kp + 1) * nf]],
    color="black",
    label="data p%i" % kp,
)
axe.scatter(
    [v[v1] / dx for v in [embedding_list_test[kp]]],
    [v[v2] / dy for v in [embedding_list_test[kp]]],
    color="red",
    label="test",
)
axe.scatter(
    [v[0][v1] / dx for v in [db["Person%i" % kp]]],
    [v[0][v2] / dy for v in [db["Person%i" % kp]]],
    color="green",
    label="avg",
)
axe.legend()
axe.set_aspect("equal")

plt.show()
