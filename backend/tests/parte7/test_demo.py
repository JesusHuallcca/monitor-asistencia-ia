"""La demo arranca el router real sin main ni una conexión externa."""
import importlib.util
from pathlib import Path
from fastapi.testclient import TestClient


def test_local_demo_auth_conversation_and_scopes():
    source=Path(__file__).resolve().parents[2]/"parte7_demo.py"
    spec=importlib.util.spec_from_file_location("parte7_demo",source)
    demo=importlib.util.module_from_spec(spec);spec.loader.exec_module(demo)
    with TestClient(demo.app) as client:
        assert client.get("/api/health").json()["mysql"]=="blocked"
        assert client.get("/").status_code==200
        assert client.get("/frontend/profesor/ia.html").status_code==200
        assert "window.location.origin" in client.get("/frontend/js/config.js").text
        assert client.get("/api/users/me").status_code==401
        token=client.post("/api/parte7-demo/session/profesor").json()["access_token"]
        headers={"Authorization":"Bearer "+token}
        assert client.get("/api/users/me",headers=headers).json()["rol"]=="profesor"
        memory=None
        for question in ["Hola","Cuáles son mis cursos","Y cuál tiene más tardanzas","Muéstrame registros de octubre"]:
            response=client.post("/api/chatbot/message",headers=headers,json={"message":question,"context_token":memory})
            assert response.status_code==200
            memory=response.json()["context"]["token"]
        assert response.json()["context"]["course_id"]==2
        assert len(response.json()["data"])==4
        forbidden=client.post("/api/chatbot/message",headers=headers,json={"message":"Mi historial","student_id":3})
        assert forbidden.status_code==403
        assert client.post("/api/parte7-demo/session/admin").status_code==404
