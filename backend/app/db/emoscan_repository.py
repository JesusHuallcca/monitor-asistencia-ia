"""Repositorio para gestionar el historial de emociones de EmoScan en MySQL.
Permite persistir y consultar las emociones asociadas a estudiante_id y usuario_id.
"""
import json
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import EmoscanHistorial, Estudiante


def registrar_historial_emocion(
    db: Session,
    usuario_id: int,
    resultado: Dict,
    origen: str = "personal",
    sesion_id: Optional[int] = None,
) -> Optional[EmoscanHistorial]:
    """Guarda una predicción de emoción en la tabla emoscan_historial vinculando el estudiante_id."""
    emocion = resultado.get("estimated_expression")
    if not emocion:
        return None

    scores = resultado.get("scores") or {}
    confianza = scores.get(emocion)
    if confianza is not None:
        confianza = round(float(confianza), 4)

    # Buscar si el usuario tiene un perfil de estudiante asociado
    estudiante = db.query(Estudiante).filter(Estudiante.usuario_id == usuario_id).first()
    estudiante_id = estudiante.id if estudiante else None

    registro = EmoscanHistorial(
        usuario_id=usuario_id,
        estudiante_id=estudiante_id,
        emocion_predominante=emocion,
        confianza=confianza,
        scores_json=json.dumps(scores),
        origen=origen,
        sesion_id=sesion_id,
        fecha_registro=datetime.utcnow(),
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro


def obtener_historial_por_estudiante(
    db: Session, estudiante_id: int, limit: int = 50
) -> List[EmoscanHistorial]:
    """Obtiene el historial de emociones para un estudiante_id específico."""
    return (
        db.query(EmoscanHistorial)
        .filter(EmoscanHistorial.estudiante_id == estudiante_id)
        .order_by(EmoscanHistorial.fecha_registro.desc())
        .limit(limit)
        .all()
    )


def obtener_historial_por_usuario(
    db: Session, usuario_id: int, limit: int = 50
) -> List[EmoscanHistorial]:
    """Obtiene el historial de emociones para el usuario en sesión."""
    return (
        db.query(EmoscanHistorial)
        .filter(EmoscanHistorial.usuario_id == usuario_id)
        .order_by(EmoscanHistorial.fecha_registro.desc())
        .limit(limit)
        .all()
    )


def obtener_resumen_emocional_estudiante(db: Session, estudiante_id: int) -> Dict:
    """Devuelve estadísticas agregadas de las emociones registradas de un estudiante."""
    total = (
        db.query(func.count(EmoscanHistorial.id))
        .filter(EmoscanHistorial.estudiante_id == estudiante_id)
        .scalar()
        or 0
    )

    conteo_emociones = (
        db.query(
            EmoscanHistorial.emocion_predominante,
            func.count(EmoscanHistorial.id),
        )
        .filter(EmoscanHistorial.estudiante_id == estudiante_id)
        .group_by(EmoscanHistorial.emocion_predominante)
        .all()
    )

    distribucion = {emocion: count for emocion, count in conteo_emociones}

    return {
        "estudiante_id": estudiante_id,
        "total_registros": total,
        "distribucion_emociones": distribucion,
    }
