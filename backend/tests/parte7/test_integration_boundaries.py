"""Regresiones de integración: permisos reales, sin MySQL ni claves externas."""
import pytest
from sqlalchemy import delete
from app.api import attendance
from app.core.config import settings
from app.db.models import Matricula
from jose import jwt

@pytest.mark.parametrize("subject", ["abc", "-1", "0", "2147483648", "١", ""])
def test_malformed_subject_rejected(harness,subject):
    client,_,_=harness
    token=jwt.encode({"sub":subject},settings.JWT_SECRET_KEY,algorithm=settings.JWT_ALGORITHM)
    assert client.get("/api/chatbot/context",headers={"Authorization":"Bearer "+token}).status_code==401

def test_attendance_professor_scope_and_revoked_enrollment(harness):
    client,sessions,headers=harness
    client.app.include_router(attendance.router)
    assert client.get("/api/attendance/",headers=headers(3)).status_code==403
    assert client.get("/api/attendance/",headers=headers(6)).json()["count"]==0
    response=client.get("/api/attendance/",headers=headers(2))
    assert response.status_code==200 and response.json()["count"]==2
    assert {r["sesion_id"] for r in response.json()["attendances"]}=={1}
    with sessions() as db:
        db.execute(delete(Matricula).where(Matricula.estudiante_id==2))
        db.commit()
    assert client.get("/api/attendance/",headers=headers(2)).json()["count"]==1
