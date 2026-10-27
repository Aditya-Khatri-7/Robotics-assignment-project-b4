"""Synthetic overhead camera and OpenCV colour-blob detector."""
import math
import cv2
import numpy as np

cv2.setNumThreads(1)

COLORS = ("red", "green", "blue")
BIN_NAMES = ("red", "green", "blue", "reject")
SHAPE_CV = 0.06    # std/mean of the contour radius: circle about 0.02, square about 0.10
BGR = {"red": (45, 45, 205), "green": (60, 180, 60), "blue": (200, 90, 40)}


class Camera:
    def __init__(self, cfg, rng):
        self.c = cfg
        self.W = int(round((cfg.cam_x1 - cfg.cam_x0) / cfg.res))
        self.H = int(round((cfg.cam_y1 - cfg.cam_y0) / cfg.res))
        # four calibration markers: noisy world coordinates -> pixel (homography, Sec. 5 of report)
        px = np.float32([[10, 10], [self.W - 10, 10], [self.W - 10, self.H - 10], [10, self.H - 10]])
        wd = np.float32([self._pix2w_exact(u, v) for u, v in px])
        wd += rng.normal(0, cfg.calib_noise, wd.shape).astype(np.float32)
        self.Hm = cv2.getPerspectiveTransform(px, wd)
        yy, xx = np.mgrid[0:self.H, 0:self.W]
        self._bg_tex = (rng.normal(0, 4, (self.H, self.W))).astype(np.float32)
        belt_v0 = int((cfg.cam_y1 - cfg.belt_y_hi) / cfg.res)
        belt_v1 = int((cfg.cam_y1 - cfg.belt_y_lo) / cfg.res)
        self.belt_rows = (belt_v0, belt_v1)

    def _pix2w_exact(self, u, v):
        c = self.c
        return (c.cam_x0 + u * c.res, c.cam_y1 - v * c.res)

    def w2pix(self, x, y):
        c = self.c
        return ((x - c.cam_x0) / c.res, (c.cam_y1 - y) / c.res)

    def render(self, objs, rng, light=1.0):
        c = self.c
        img = np.full((self.H, self.W, 3), 40, np.uint8)
        v0, v1 = self.belt_rows
        img[v0:v1] = (95, 95, 95)
        img[v0:v0 + 2] = (30, 30, 30)
        img[v1 - 2:v1] = (30, 30, 30)
        for o in objs:
            u, v = self.w2pix(o["x"], o["y"])
            if o.get("shape") == "circle":
                cv2.circle(img, (int(round(u * 16)), int(round(v * 16))), int(round(c.cyl_r / c.res * 16)), BGR[o["color"]], -1, cv2.LINE_AA, 4)
                continue
            hs = 0.5 * c.cube / c.res
            ct, st = math.cos(o["th"]), math.sin(o["th"])
            pts = np.array([[u + ct * a - st * b, v + st * a + ct * b]
                            for a, b in ((-hs, -hs), (hs, -hs), (hs, hs), (-hs, hs))], np.float32)
            cv2.fillPoly(img, [np.round(pts * 16).astype(np.int32)], BGR[o["color"]], cv2.LINE_AA, 4)
        f = img.astype(np.float32) * light + self._bg_tex[..., None]
        f += rng.normal(0, c.img_noise, f.shape).astype(np.float32)
        return np.clip(f, 0, 255).astype(np.uint8)

    def detect(self, img):
        """Return list of (x, y, color, area_px, shape) in world coordinates; shape is "square" or "circle"."""
        blur = cv2.GaussianBlur(img, (5, 5), 0)
        hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
        sat_ok = hsv[..., 1] > 90
        val_ok = hsv[..., 2] > 50
        h = hsv[..., 0]
        masks = {
            "red": ((h < 8) | (h > 172)) & sat_ok & val_ok,
            "green": (h > 45) & (h < 85) & sat_ok & val_ok,
            "blue": (h > 95) & (h < 125) & sat_ok & val_ok,
        }
        out = []
        k = np.ones((3, 3), np.uint8)
        for name, m in masks.items():
            m = cv2.morphologyEx(m.astype(np.uint8) * 255, cv2.MORPH_OPEN, k)
            n, labels, stats, cent = cv2.connectedComponentsWithStats(m, connectivity=8)
            for i in range(1, n):
                area = stats[i, cv2.CC_STAT_AREA]
                if area < 0.3 * (self.c.cube / self.c.res) ** 2:
                    continue
                # centroid of a partly visible object is biased: skip blobs touching the image border
                x0, y0, w, hgt = (stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP],
                                  stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT])
                if x0 <= 0 or y0 <= 0 or x0 + w >= self.W or y0 + hgt >= self.H:
                    continue
                u, v = cent[i]
                # shape feature: variation of the contour radius around the centroid (circle about 0.02, square about 0.10)
                sub = (labels[y0:y0 + hgt, x0:x0 + w] == i).astype(np.uint8)
                cs, _ = cv2.findContours(sub, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
                cnt = max(cs, key=cv2.contourArea)[:, 0, :].astype(float)
                rad = np.hypot(cnt[:, 0] + x0 - u, cnt[:, 1] + y0 - v)
                shape = "circle" if rad.std() / rad.mean() < SHAPE_CV else "square"
                p = self.Hm @ np.array([u, v, 1.0])
                out.append((float(p[0] / p[2]), float(p[1] / p[2]), name, int(area), shape))
        return out
