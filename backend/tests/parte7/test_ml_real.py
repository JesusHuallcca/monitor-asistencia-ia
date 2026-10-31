"""Inferencia TensorFlow real sobre fixture histórica sintética autorizada."""
import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session
from fastapi import HTTPException
from red_neuronal.tests.test_system import env as neural_env
from app.db.models import Usuario,AsignacionProfesor
from app.services.chatbot_ml import neural_prediction

def test_chatbot_real_neural_inference_and_revocation(neural_env):
    with Session(neural_env.engine) as db:
        user=db.get(Usuario,1)
        result=neural_prediction(db,user,{"course_id":1,"student_id":1})
        assert result["status"]=="available"
        assert 0 <= result["probability"] <= 1
        assert result["training_origin"]=="sintetico"
        assert result["model_version"]=="parte6-dense-9x32x16x1-v1"
        assert len(result["variables"])==9
        db.execute(delete(AsignacionProfesor).where(AsignacionProfesor.profesor_id==1))
        db.commit()
        with pytest.raises(HTTPException) as failure:
            neural_prediction(db,user,{"course_id":1,"student_id":1})
        assert failure.value.status_code==403
