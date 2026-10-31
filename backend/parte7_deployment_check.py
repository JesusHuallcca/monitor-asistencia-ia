"""Comprobación LOCAL de despliegue. No inicia app.main ni conecta MySQL."""
import ctypes
import hashlib
import json
import platform
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))


def memory():
    """RSS/working set del proceso en Windows; no extrapola al contenedor Linux."""
    if sys.platform != "win32":
        return {"available": False, "reason": "Esta medición utiliza contadores de Windows."}
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
        ]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        return {"available": False}
    return {"available": True, "working_set_mib": round(counters.WorkingSetSize / 2**20, 2),
            "peak_working_set_mib": round(counters.PeakWorkingSetSize / 2**20, 2)}


def main():
    # Este módulo impone SQLite RAM, credenciales ficticias y rechazo de conexiones MySQL.
    from parte7_demo import app
    from fastapi.testclient import TestClient
    from datetime import date
    after_import = memory()
    exports = {}
    with TestClient(app) as client:
        health = client.get("/api/health").json()
        assert health["demo"] and health["mysql"] == "blocked"
        token = client.post("/api/parte7-demo/session/profesor").json()["access_token"]
        headers = {"Authorization": "Bearer " + token}  # Solo memoria; nunca se imprime.
        year = date.today().year
        response = client.post("/api/chatbot/reports", headers=headers, json={
            "report_type": "asistencia", "course_id": 2,
            "period_start": f"{year}-09-01", "period_end": f"{year}-10-31"})
        assert response.status_code == 200
        preview = response.json()
        assert preview["synthetic"] and preview["report_rows"] == 8
        for fmt in ("xlsx", "pdf", "docx"):
            response = client.post(f"/api/chatbot/reports/{preview['id']}/exports/{fmt}", headers=headers)
            assert response.status_code == 200
            file = response.json()
            download = client.get(file["url"], headers=headers)
            assert download.status_code == 200
            assert hashlib.sha256(download.content).hexdigest() == file["file_sha256"]
            exports[fmt] = {"bytes": len(download.content), "authorized_download": True}
        after_exports = memory()

    # Prueba matemática aislada de la estrategia propuesta; NO modifica face_crypto.
    from cryptography.fernet import Fernet, MultiFernet, InvalidToken
    old, new = Fernet(Fernet.generate_key()), Fernet(Fernet.generate_key())
    original = b"synthetic-embedding-not-a-student"
    encrypted = old.encrypt(original)
    try:
        new.decrypt(encrypted)
    except InvalidToken:
        rejected_without_old_key = True
    else:
        raise AssertionError("Una clave diferente no debe descifrar el original.")
    rotated = MultiFernet([new, old]).rotate(encrypted)
    assert new.decrypt(rotated) == original
    assert old.decrypt(encrypted) == original  # Copia anterior recuperable con su clave.
    try:
        old.decrypt(rotated)
    except InvalidToken:
        pass
    else:
        raise AssertionError("La copia rotada no debe depender de la clave antigua.")

    result = {
        "scope": "local_synthetic_only", "python": platform.python_version(),
        "platform": platform.system(), "mysql": "blocked", "render_modified": False,
        "memory_after_demo_import": after_import,
        "memory_after_eight_row_exports": after_exports,
        "memory_limitations": "Una petición a la vez; sin TensorFlow/ONNX, sin carga máxima, no es dimensionamiento Linux.",
        "exports": exports,
        "rotation_strategy_test": {
            "wrong_key_rejected": rejected_without_old_key,
            "rotated_ciphertext_decrypts_with_new_key": True,
            "old_backup_decrypts_with_preserved_old_key": True,
            "production_keyring_implemented": False,
        },
    }
    target = ROOT / "docs" / "parte7" / "despliegue" / "PRECHECK_LOCAL.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
