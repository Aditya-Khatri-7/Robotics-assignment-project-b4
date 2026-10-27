import math
from sortarm.simcs import SimCS
from sortarm.sim import M3

s = SimCS(M3, 0.15, 3, n_obj=5)
orig = s._cam_frame
log = []


def cf(t, light):
    d = orig(t, light)
    truth = [(o["id"], round(o["x"], 3), round(o["y"], 3), o["color"][0], o["shape"][0]) for o in s.objs if o["state"] == "belt"]
    if int(t * 20) % 20 == 0:
        print("t=%.2f light=%.2f dets=%s truth=%s" % (t, light, [(round(a[0], 3), round(a[1], 3), a[2][0], a[4][0]) for a in d], truth))
    return d


s._cam_frame = cf
r = s.run(t_max=7)
print("tracks", [(tr.id, tr.hits, tr.color, tr.shape) for tr in s.tracker.tracks])
s.close()
