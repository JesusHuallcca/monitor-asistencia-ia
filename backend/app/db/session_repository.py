from datetime import date, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import SesionClase


class SessionRepository:

    def create(
        self,
        db: Session,
        curso_id: int,
        fecha: date,
        hora_inicio: time,
        hora_fin: time,
        tolerancia_minutos: int,
    ):
        sesion = SesionClase(
            curso_id=curso_id,
            fecha=fecha,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            tolerancia_minutos=tolerancia_minutos,
            estado="ACTIVA",
        )

        db.add(sesion)
        db.commit()
        db.refresh(sesion)

        return sesion

    def find_by_id(self, db: Session, sesion_id: int):
        return db.get(SesionClase, sesion_id)

    def find_active(
        self,
        db: Session,
        current_date: date,
        current_time: time,
    ):
        statement = (
            select(SesionClase)
            .where(
                SesionClase.fecha == current_date,
                SesionClase.estado == "ACTIVA",
                SesionClase.hora_inicio <= current_time,
                SesionClase.hora_fin > current_time,
            )
            .order_by(SesionClase.hora_inicio)
            .limit(1)
        )

        return db.execute(statement).scalar_one_or_none()

    def find_by_date(
        self,
        db: Session,
        current_date: date,
    ):
        statement = (
            select(SesionClase)
            .where(
                SesionClase.fecha == current_date
            )
            .order_by(SesionClase.hora_inicio)
        )

        return db.execute(statement).scalars().all()

    def find_expired_active_sessions(
        self,
        db: Session,
        current_date: date,
        current_time: time,
    ):
        statement = (
            select(SesionClase)
            .where(
                SesionClase.fecha == current_date,
                SesionClase.estado == "ACTIVA",
                SesionClase.hora_fin <= current_time,
            )
        )

        return db.execute(statement).scalars().all()


session_repository = SessionRepository()