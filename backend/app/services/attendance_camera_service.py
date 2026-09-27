from backend.app.services.face_service import face_service
from backend.app.services.liveness_service import liveness_service
from backend.app.services.attendance_service import attendance_service


class AttendanceCameraService:

    def __init__(self):
        self.last_person_id = None
        self.recognition_count = 0
        self.required_recognitions = 3

    def reset(self):
        self.last_person_id = None
        self.recognition_count = 0

        liveness_service.detector.previous_frame = None

    def process_frame(self, frame):
        faces = face_service.detect(frame)

        if len(faces) == 0:
            return {
                "status": "NO_FACE",
                "message": "No se detectó ningún rostro"
            }

        if len(faces) > 1:
            return {
                "status": "MULTIPLE_FACES",
                "message": "Debe haber un solo rostro"
            }

        detected_face = faces[0]

        face_image = face_service.extract_face(
            frame,
            detected_face
        )

        if face_image.size == 0:
            return {
                "status": "INVALID_FACE",
                "message": "No se pudo extraer el rostro"
            }

        recognition = face_service.recognize(face_image)

        if recognition is None:
            self.reset()

            return {
                "status": "UNKNOWN_FACE",
                "message": "Rostro no reconocido"
            }

        liveness = liveness_service.check(frame)

        person_id = recognition["person_id"]

        if self.last_person_id != person_id:
            self.last_person_id = person_id
            self.recognition_count = 1
        else:
            self.recognition_count += 1

        if not liveness["is_live"]:
            return {
                "status": "LIVENESS_PENDING",
                "person_id": person_id,
                "confidence": recognition["confidence"],
                "liveness": liveness,
                "recognitions": self.recognition_count,
                "required": self.required_recognitions
            }

        if self.recognition_count < self.required_recognitions:
            return {
                "status": "RECOGNITION_PENDING",
                "person_id": person_id,
                "confidence": recognition["confidence"],
                "liveness": liveness,
                "recognitions": self.recognition_count,
                "required": self.required_recognitions
            }

        result = attendance_service.register(
            person_id=person_id,
            confidence=recognition["confidence"],
            liveness_score=liveness["score"]
        )

        self.reset()

        return {
            **result,
            "recognition": recognition,
            "liveness": liveness
        }


attendance_camera_service = AttendanceCameraService()