from datetime import datetime, time

from backend.app.db.attendance_repository import attendance_repository


class AttendanceService:

    def __init__(self):
        self.attendances = []

        self.schedule = {
            "MONDAY": (time(7, 0), time(22, 0)),
            "TUESDAY": (time(7, 0), time(22, 0)),
            "WEDNESDAY": (time(7, 0), time(22, 0)),
            "THURSDAY": (time(7, 0), time(22, 0)),
            "FRIDAY": (time(7, 0), time(22, 0)),
            "SATURDAY": (time(7, 0), time(22, 0)),
            "SUNDAY": (time(7, 0), time(22, 0))
        }

    def is_within_schedule(self, current_datetime=None):
        if current_datetime is None:
            current_datetime = datetime.now()

        day_name = current_datetime.strftime("%A").upper()

        start_time, end_time = self.schedule[day_name]

        current_time = current_datetime.time()

        return start_time <= current_time <= end_time

    def already_registered(self, person_id, current_date=None):
        return attendance_repository.exists_today(
            person_id,
            current_date
        )

    def register(
        self,
        person_id,
        confidence,
        liveness_score,
        course_id=None,
        session_id=None
    ):
        now = datetime.now()

        person_id = str(person_id)

        if course_id is not None:
            course_id = str(course_id)

        if session_id is not None:
            session_id = str(session_id)

        if not self.is_within_schedule(now):
            return {
                "success": False,
                "status": "OUT_OF_SCHEDULE",
                "message": "La asistencia está fuera del horario permitido"
            }

        if self.already_registered(
            person_id,
            now.date()
        ):
            return {
                "success": False,
                "status": "ALREADY_REGISTERED",
                "message": "La asistencia ya fue registrada"
            }

        attendance_id = attendance_repository.save(
            person_id=person_id,
            attendance_date=now.date(),
            attendance_time=now.time().replace(microsecond=0),
            confidence=confidence,
            liveness_score=liveness_score,
            status="PRESENTE"
        )

        attendance = {
            "id": attendance_id,
            "person_id": person_id,
            "date": str(now.date()),
            "time": now.strftime("%H:%M:%S"),
            "confidence": round(
                float(confidence),
                4
            ),
            "liveness_score": round(
                float(liveness_score),
                4
            ),
            "status": "PRESENTE"
        }

        if course_id is not None:
            attendance["course_id"] = course_id

        if session_id is not None:
            attendance["session_id"] = session_id

        self.attendances.append(attendance)

        return {
            "success": True,
            "status": "REGISTERED",
            "message": "Asistencia registrada correctamente",
            "attendance": attendance
        }

    def get_all(self):
        records = attendance_repository.find_all()

        attendances = []

        for record in records:
            hora = record["hora"]

            if hasattr(hora, "total_seconds"):
                total_seconds = int(
                    hora.total_seconds()
                )

                hours = total_seconds // 3600
                minutes = (
                    total_seconds % 3600
                ) // 60
                seconds = total_seconds % 60

                time_string = (
                    f"{hours:02d}:"
                    f"{minutes:02d}:"
                    f"{seconds:02d}"
                )
            else:
                time_string = str(hora)

            attendances.append({
                "id": record["id"],
                "person_id": record["person_id"],
                "date": str(record["fecha"]),
                "time": time_string,
                "confidence": float(
                    record["confianza"]
                ),
                "liveness_score": float(
                    record["liveness_score"]
                ),
                "status": record["estado"]
            })

        return attendances

    def clear(self):
        self.attendances.clear()


attendance_service = AttendanceService()