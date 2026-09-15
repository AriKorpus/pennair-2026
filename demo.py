# Show the detector's output on an image or a video. Detection lives in algorithm.py.
# python3 demo.py image10.png
# python3 demo.py video10.mp4   
import sys
import time

import cv2

import algorithm

WINDOW = "detections"


def main(path):
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW, 1280, 720)

    image = cv2.imread(path)                    
    if image is not None:
        cv2.imshow(WINDOW, algorithm.draw(image, algorithm.detect(image)))
        cv2.waitKey(0)
    else:
        cap = cv2.VideoCapture(path)
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            t0 = time.perf_counter()
            out = algorithm.draw(frame, algorithm.detect(frame))
            fps = 1.0 / (time.perf_counter() - t0)
            cv2.putText(out, "%.0f fps" % fps, (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
            cv2.imshow(WINDOW, out)
            if cv2.waitKey(1) == ord("q"):
                break
        cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main(sys.argv[1])
