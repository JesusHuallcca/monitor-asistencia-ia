from datetime import date, datetime, time

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models import Asistencia, Curso, Estudiante, Matricula
from app.db.session_repository import session_repository


class SessionService:

    def crear_sesion(
        self,
        db: Session,
        curso_id: int,
        fecha: date,
        hora_inicio: time,
        hora_fin: time,
        tolerancia_minutos: int,
    ):
        curso = db.get(Curso, curso_id)

        if curso is None:
            raise HTTPException(
                status_code=404,
                detail="Curso no encontrado"
            )

        if not curso.activo:
            raise HTTPException(
                status_code=400,
                detail="El curso no está activo"
            )

        if hora_fin <= hora_inicio:
            raise HTTPException(
                status_code=400,
                detail="La hora de fin debe ser posterior a la hora de inicio"
            )

        sesiones = session_repository.find_by_date(
            db=db,
            current_date=fecha
        )

        for sesion in sesiones:
            if sesion.curso_id != curso_id:
                continue

            if sesion.estado == "CANCELADA":
                continue

            if (
                hora_inicio < sesion.hora_fin
                and hora_fin > sesion.hora_inicio
            ):
                raise HTTPException(
                    status_code=409,
                    detail="Ya existe una sesión que se cruza con este horario"
                )

        return session_repository.create(
            db=db,
            curso_id=curso_id,
            fecha=fecha,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            tolerancia_minutos=tolerancia_minutos,
        )

    def obtener_sesion_actual(
        self,
        db: Session,
        current_date: date | None = None,
        current_time: time | None = None,
    ):
        ahora = datetime.now()

        if current_date is None:
            current_date = ahora.date()

        if current_time is None:
            current_time = ahora.time()

        self.cerrar_sesiones_vencidas(
            db=db,
            current_date=current_date,
            current_time=current_time,
        )

        return session_repository.find_active(
            db=db,
            current_date=current_date,
            current_time=current_time,
        )

    def cerrar_sesiones_vencidas(
        self,
        db: Session,
        current_date: date,
        current_time: time,
    ):
        sesiones = session_repository.find_expired_active_sessions(
            db=db,
            current_date=current_date,
            current_time=current_time,
        )

        cerradas = []

        for sesion in sesiones:
            self.generar_ausentes(
                db=db,
                sesion_id=sesion.id,
                curso_id=sesion.curso_id,
                fecha=sesion.fecha,
            )

            sesion.estado = "CERRADA"
            cerradas.append(sesion)

        if cerradas:
            db.commit()

        return cerradas

    def generar_ausentes(
        self,
        db: Session,
        sesion_id: int,
        curso_id: int,
        fecha: date,
    ):
        matriculas = (
            db.query(Matricula)
            .filter(Matricula.curso_id == curso_id)
            .all()
        )

        creados = 0

        for matricula in matriculas:
            estudiante = db.get(
                Estudiante,
                matricula.estudiante_id
            )

            if estudiante is None:
                continue

            usuario_id = estudiante.usuario_id

            existe = (
                db.query(Asistencia.id)
                .filter(
                    Asistencia.usuario_id == usuario_id,
                    Asistencia.sesion_id == sesion_id,
                )
                .first()
            )

            if existe is not None:
                continue

            ausencia = Asistencia(
                usuario_id=usuario_id,
                sesion_id=sesion_id,
                fecha=fecha,
                hora=self._hora_cierre(),
                confianza=0,
                liveness_score=0,
                estado="AUSENTE",
            )

            db.add(ausencia)
            creados += 1

        return creados

    def _hora_cierre(self):
        return datetime.now().time().replace(microsecond=0)

    def obtener_sesion(
        self,
        db: Session,
        sesion_id: int
    ):
        return session_repository.find_by_id(
            db=db,
            sesion_id=sesion_id
        )

    def obtener_sesiones_fecha(
        self,
        db: Session,
        fecha: date
    ):
        return session_repository.find_by_date(
            db=db,
            current_date=fecha
        )


session_service = SessionService()