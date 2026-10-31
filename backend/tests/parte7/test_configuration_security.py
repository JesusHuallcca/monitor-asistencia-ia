"""Secrets are explicit; this test uses no external provider."""
from pathlib import Path
from app.core.config import settings
from app.core import security
import pytest

def test_empty_jwt_key_cannot_issue_or_accept_tokens(monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", "")
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        security.create_access_token(1, "profesor")
    assert security.decode_access_token("untrusted") is None

def test_blueprint_has_no_literal_secret_values():
    import yaml
    root = Path(__file__).resolve().parents[3]
    data = yaml.safe_load((root / "render.yaml").read_text(encoding="utf-8"))
    for service in data.get("services", []):
        for field in service.get("envVars", []):
            if any(word in field.get("key", "") for word in ("PASSWORD","SECRET","ENCRYPTION_KEY","API_KEY")):
                assert not field.get("value")

def isolated_main_handler(name):
    # Execute the original handler body without loading model-download lifespan.
    import ast
    root = Path(__file__).resolve().parents[3]
    tree = ast.parse((root / "backend/app/main.py").read_text(encoding="utf-8"))
    function = next(node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name)
    function.decorator_list = []
    module = ast.Module(body=[function], type_ignores=[])
    namespace = {}
    exec(compile(ast.fix_missing_locations(module), "<main-handler-under-test>", "exec"), namespace)
    return namespace[name]

def test_public_health_never_returns_connection_diagnostics():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    app = FastAPI()
    app.get("/api/health")(isolated_main_handler("health"))
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert not {"host","user","pass_prefix","pass_len","db_error","has_fallback"} & response.json().keys()

def test_public_error_never_returns_exception_content(caplog):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    app = FastAPI()
    app.add_exception_handler(Exception, isolated_main_handler("unhandled_exception_handler"))
    @app.get("/failure")
    def failure():
        raise RuntimeError("sensitive-synthetic-test-content")
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/failure")
    assert response.status_code == 500
    assert "sensitive-synthetic-test-content" not in response.text
    assert "sensitive-synthetic-test-content" not in caplog.text
