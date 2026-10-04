from datetime import datetime

from sqlalchemy.orm import Session

from app.db.attendance_repository import attendance_repository


class AttendanceService:

    def register(
        self,
        db: Session,
        usuario_id: int,
        confidence: float,
        liveness_score: float
    ):
        now = datetime.now()

        session = attendance_repository.find_active_session(
            db=db,
            current_date=now.date(),
            current_time=now.time()
        )

        if session is None:
            return {
                "success": False,
                "status": "NO_ACTIVE_SESSION",
                "message": "No hay una sesión de clase activa en este momento"
            }

        if attendance_repository.exists_in_session(
            db=db,
            usuario_id=usuario_id,
            sesion_id=session.id
        ):
            return {
                "success": False,
                "status": "ALREADY_REGISTERED",
                "message": "La asistencia ya fue registrada para esta sesión"
            }

        llegada = now.time()

        tolerancia = session.tolerancia_minutos

        inicio_minutos = (
            session.hora_inicio.hour * 60
            + session.hora_inicio.minute
        )

        llegada_minutos = (
            llegada.hour * 60
            + llegada.minute
        )

        diferencia = llegada_minutos - inicio_minutos

        if diferencia > tolerancia:
            estado = "TARDANZA"
        else:
            estado = "PRESENTE"

        asistencia = attendance_repository.save(
            db=db,
            usuario_id=usuario_id,
            sesion_id=session.id,
            attendance_date=now.date(),
            attendance_time=llegada.replace(microsecond=0),
            confidence=confidence,
            liveness_score=liveness_score,
            status=estado
        )

        return {
            "success": True,
            "status": "REGISTERED",
            "message": "Asistencia registrada correctamente",
            "attendance": {
                "id": asistencia.id,
                "usuario_id": asistencia.usuario_id,
                "sesion_id": asistencia.sesion_id,
                "fecha": str(asistencia.fecha),
                "hora": str(asistencia.hora),
                "confianza": round(float(asistencia.confianza), 4),
                "liveness_score": round(float(asistencia.liveness_score), 4),
                "estado": asistencia.estado
            }
        }

    def get_all(self, db: Session):
        records = attendance_repository.find_all(db)

        attendances = []

        for record in records:
            attendances.append({
                "id": record.id,
                "usuario_id": record.usuario_id,
                "sesion_id": record.sesion_id,
                "fecha": str(record.fecha),
                "hora": str(record.hora),
                "confianza": float(record.confianza),
                "liveness_score": float(record.liveness_score),
                "estado": record.estado
            })

        return attendances

    def get_my_course_attendance(
        self,
        db: Session,
        usuario_id: int,
        curso_id: int
    ):
        records = attendance_repository.find_by_user_and_course(
            db=db,
            usuario_id=usuario_id,
            curso_id=curso_id
        )

        valores = {
            "PRESENTE": 100,
            "TARDANZA": 50,
            "AUSENTE": 0
        }

        registros = []

        for record in records:
            estado = record.estado.upper()

            registros.append({
                "id": record.id,
                "sesion_id": record.sesion_id,
                "fecha": str(record.fecha),
                "hora": str(record.hora),
                "estado": estado,
                "calificacion": valores.get(estado, 0)
            })

        promedio = None

        if registros:
            promedio = sum(
                registro["calificacion"]
                for registro in registros
            ) / len(registros)

        presentes = sum(
            1
            for registro in registros
            if registro["estado"] == "PRESENTE"
        )

        return {
            "curso_id": curso_id,
            "promedio": round(promedio, 2) if promedio is not None else None,
            "presentes": presentes,
            "registros": registros
        }


attendance_service = AttendanceService()