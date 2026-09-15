# Shape detection and 3D localisation. Plain OpenCV, no ROS.
import cv2
import numpy as np

MIN_AREA = 0.0015  # smallest accepted object, as a fraction of the frame
MAX_AREA = 0.35    # a region larger than this is background, not an object
SPAN = 0.95        # one reaching this far across the frame is background as well
UNIFORM = 0.4      # objects are this much calmer than a typical neighborhood
NOISE = 0.5        # sensor noise floor, in grey levels
SEAM = 0.7         # an inner edge parts two objects at this share of outline contrast
BAND = 5           # how far past the seeds watershed may search, in erosions of K
PAD = 16           # slack around a seed's bounding box, in pixels

CAMERA = np.array([[2564.3186869, 0, 0],     # camera intrinsics, as supplied
                   [0, 2569.70273111, 0],
                   [0, 0, 1]])
CALIB_W = 1920     # width the intrinsics were calibrated at; focal length scales with it
RADIUS = 10.0      # the circle's true radius, inches -- this is what sets the scale
ROUND = 0.85       # fill fraction above which a contour is taken to be that circle
DEPTH = 251.4      # last depth seen, inches; held for frames with no circle in view

K = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
GREEN, CYAN = (0, 255, 0), (255, 255, 0)


def focal(width):
    # Focal length is in pixels, so it scales if the frame is not the calibrated width.
    return CAMERA[0, 0] * width / CALIB_W, CAMERA[1, 1] * width / CALIB_W


def depth(found, fx):
    # Distance to the ground, recovered from the circle, whose true radius we know. We
    # identify it as the contour that most completely fills its own enclosing circle, and
    # skip any touching the frame edge, since a clipped circle measures too small.
    global DEPTH
    fill, area = max(((M["m00"] / (np.pi * cv2.minEnclosingCircle(c)[1] ** 2), M["m00"])
                      if whole else (0, 0) for c, M, whole in found), default=(0, 0))
    if fill >= ROUND:
        DEPTH = fx * RADIUS / np.sqrt(area / np.pi)   # update the held value
    return DEPTH


def detect(frame):
    # Finds every object and returns its outline plus its center in inches from the
    # camera, measured from the middle of the image: X right, Y down, Z forward.
    h, w = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 1. measure how much fine detail sits around each pixel
    texture = cv2.boxFilter(cv2.absdiff(gray, cv2.blur(gray, (9, 9))), cv2.CV_32F, (9, 9))
    # 2. objects are the smooth pixels. The threshold is a fraction of this frame's own
    #    median, so it adapts to grass or asphalt without being changed.
    mask = np.uint8(texture < max(UNIFORM * np.median(texture[::4, ::4]), NOISE)) * 255

    # 3. find color edges: Scharr on each channel, keep the strongest response
    xs, ys = (cv2.split(cv2.Scharr(cv2.pyrDown(frame), cv2.CV_32F, d, 1 - d)) for d in (1, 0))
    edge = cv2.resize(cv2.max(cv2.max(cv2.magnitude(xs[0], ys[0]), cv2.magnitude(xs[1], ys[1])),
                              cv2.magnitude(xs[2], ys[2])), (w, h))

    # 4. erode the mask to pixels certainly inside an object, and dilate it to mark where
    #    the background certainly starts. We remove specks before dilating, since each one
    #    would otherwise add its own region for watershed to resolve.
    inner = cv2.erode(mask, K)
    outer = cv2.dilate(cv2.morphologyEx(inner, cv2.MORPH_OPEN, K), K, iterations=BAND)

    # 5. measure how strong a normal object outline is in this frame, then delete pixels
    #    lying on any edge of comparable strength. Where two shapes overlap this deletes
    #    the seam between them.
    ref = np.percentile(edge[(outer > 0) & (inner == 0)], 75)
    cut = cv2.morphologyEx(inner & (np.uint8(edge < SEAM * ref) * 255), cv2.MORPH_OPEN, K)

    # 6. number each object. If deleting the seam broke a region into two sizeable pieces,
    #    it was two overlapping objects and we label them separately. A thin sliver instead
    #    means one patterned object, so we keep it whole.
    floor = 0.3 * MIN_AREA * h * w
    n, comp, stats, _ = cv2.connectedComponentsWithStats(inner)
    markers, boxes = np.zeros(comp.shape, np.int32), []
    for i in range(1, n):
        if stats[i, 4] < floor:
            continue
        x, y, bw, bh = stats[i, :4]
        box = (slice(max(y - PAD, 0), y + bh + PAD), slice(max(x - PAD, 0), x + bw + PAD))
        seed = np.uint8(comp[box] == i) * 255
        k, sub, st, _ = cv2.connectedComponentsWithStats(cut[box] & seed)
        keep = [j for j in range(1, k) if st[j, 4] >= floor]
        for part in ([sub == j for j in keep] if len(keep) > 1 else [seed > 0]):
            boxes.append(box)
            markers[box][part] = len(boxes) + 1

    # 7. grow each marker outward until its border reaches a real edge
    markers[outer == 0] = 1
    cv2.watershed(frame, markers)

    # 8. trace each region's outline, throwing out anything too small, too big, or wide
    #    enough to be the background
    found = []
    for i, box in enumerate(boxes):
        blob = np.uint8(markers[box] == i + 2) * 255
        for c in cv2.findContours(blob, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
            c += (box[1].start, box[0].start)
            M, (x, y, bw, bh) = cv2.moments(c), cv2.boundingRect(c)
            if MIN_AREA * h * w <= M["m00"] <= MAX_AREA * h * w and bw < SPAN * w and bh < SPAN * h:
                found.append((c, M, x > 1 and y > 1 and x + bw < w - 1 and y + bh < h - 1))

    # 9. the circle's known radius gives the distance to the ground. The ground is flat, so
    #    every shape lies at that depth, and we convert each center from pixels to inches.
    fx, fy = focal(w)
    z = depth(found, fx)
    return [(c, ((M["m10"] / M["m00"] - w / 2) * z / fx,
                 (M["m01"] / M["m00"] - h / 2) * z / fy, z)) for c, M, _ in found]


def draw(frame, found):
    # green outline, cyan center dot, cyan (x", y", z") label
    h, w = frame.shape[:2]
    fx, fy = focal(w)
    for c, (x, y, z) in found:
        u, v = int(x * fx / z + w / 2), int(y * fy / z + h / 2)   
        tag = '(%.1f", %.1f", %.1f")' % (x, y, z)
        tw = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0][0]
        cv2.drawContours(frame, [c], -1, GREEN, 4)
        cv2.circle(frame, (u, v), 7, CYAN, -1)
        cv2.putText(frame, tag, (min(u + 14, w - tw - 8), max(v - 14, 26)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, CYAN, 2)
    return frame
