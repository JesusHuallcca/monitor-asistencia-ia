import cv2
import numpy as np


class LivenessDetector:
    def __init__(self, threshold=8.0):
        self.threshold = threshold
        self.previous_frame = None

    def check(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (160, 120))

        if self.previous_frame is None:
            self.previous_frame = gray
            return {
                "is_live": False,
                "score": 0.0
            }

        difference = cv2.absdiff(self.previous_frame, gray)
        score = float(np.mean(difference))

        self.previous_frame = gray

        return {
            "is_live": score >= self.threshold,
            "score": score
        }


def check_liveness(frame, detector=None):
    if detector is None:
        detector = LivenessDetector()

    return detector.check(frame)