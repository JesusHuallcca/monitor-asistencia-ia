from ai.face.liveness import LivenessDetector


class LivenessService:
    def __init__(self):
        self.detector = LivenessDetector()

    def check(self, frame):
        return self.detector.check(frame)


liveness_service = LivenessService()