from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Asistencia, SesionClase


class AttendanceRepository:

    def save(
        self,
        db: Session,
        usuario_id: int,
        sesion_id: int,
        attendance_date: date,
        attendance_time,
        confidence: float,
        liveness_score: float,
        status: str
    ):
        asistencia = Asistencia(
            usuario_id=usuario_id,
            sesion_id=sesion_id,
            fecha=attendance_date,
            hora=attendance_time,
            confianza=confidence,
            liveness_score=liveness_score,
            estado=status
        )

        db.add(asistencia)
        db.commit()
        db.refresh(asistencia)

        return asistencia

    def exists_in_session(
        self,
        db: Session,
        usuario_id: int,
        sesion_id: int
    ) -> bool:
        statement = (
            select(Asistencia.id)
            .where(
                Asistencia.usuario_id == usuario_id,
                Asistencia.sesion_id == sesion_id
            )
            .limit(1)
        )

        return db.execute(statement).scalar_one_or_none() is not None

    def find_all(self, db: Session):
        statement = (
            select(Asistencia)
            .order_by(
                Asistencia.fecha.desc(),
                Asistencia.hora.desc()
            )
        )

        return db.execute(statement).scalars().all()

    def find_active_session(
        self,
        db: Session,
        current_date: date,
        current_time
    ):
        statement = (
            select(SesionClase)
            .where(
                SesionClase.fecha == current_date,
                SesionClase.estado == "ACTIVA",
                SesionClase.hora_inicio <= current_time,
                SesionClase.hora_fin >= current_time
            )
            .order_by(SesionClase.hora_inicio)
            .limit(1)
        )

        return db.execute(statement).scalar_one_or_none()


attendance_repository = AttendanceRepository()
