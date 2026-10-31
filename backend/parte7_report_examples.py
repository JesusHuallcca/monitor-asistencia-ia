"""Ejemplos permanentes SOLO sintéticos; las exportaciones normales viven en RAM."""
from datetime import date
from io import BytesIO
import hashlib
import json
from pathlib import Path
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from pypdf import PdfReader
from docx import Document
from parte7_demo import app

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/"docs"/"parte7"/"ejemplos"

def main():
    TARGET.mkdir(parents=True,exist_ok=True)
    with TestClient(app) as client:
        token=client.post("/api/parte7-demo/session/profesor").json()["access_token"]
        headers={"Authorization":"Bearer "+token}
        year=date.today().year
        response=client.post("/api/chatbot/reports",headers=headers,json={"report_type":"asistencia","course_id":2,"period_start":f"{year}-09-01","period_end":f"{year}-10-31"})
        assert response.status_code==200,response.text
        report=response.json();key=report["id"]
        assert report["synthetic"] and report["report_rows"]==8
        assert {row["estudiante"] for row in report["rows"]}=={"Ana Sintético"}
        assert report["metrics"]["asistencia_pct"]==87.5
        files={};manifest={"synthetic":True,"source":report["source"],"spec":report["spec"],"generated_at":report["generated_at"],"dataset_sha256":report["fingerprint"],"metrics":report["metrics"],"rows":report["report_rows"],"files":{}}
        for fmt in ("xlsx","pdf","docx"):
            exported=client.post(f"/api/chatbot/reports/{key}/exports/{fmt}",headers=headers)
            assert exported.status_code==200,exported.text
            file=exported.json();download=client.get(file["url"],headers=headers)
            assert download.status_code==200
            assert download.headers["x-report-dataset-sha256"]==report["fingerprint"]
            assert hashlib.sha256(download.content).hexdigest()==file["file_sha256"]
            name=f"ejemplo-asistencia-autorizada.{fmt}"
            (TARGET/name).write_bytes(download.content);files[fmt]=download.content
            manifest["files"][fmt]={"name":name,"bytes":len(download.content),"sha256":file["file_sha256"]}
        wb=load_workbook(BytesIO(files["xlsx"]));assert wb["Registros"].max_row==9 and wb["Indicadores"]["B8"].value==87.5
        text="\n".join(page.extract_text() for page in PdfReader(BytesIO(files["pdf"])).pages)
        assert "87,50" in text and "Ana Sintético" in text and report["fingerprint"] in text
        document=Document(BytesIO(files["docx"]));assert len(document.tables[1].rows)==9
        assert "87,50" in " ".join(cell.text for table in document.tables for row in table.rows for cell in row.cells)
        manifest["verified"]=["Autenticación y curso autorizado","8 filas idénticas de prueba","Misma huella de dataset en los tres formatos","Lectura independiente con openpyxl, pypdf y python-docx","7 asistencias (2 presentes + 5 tardanzas) / 8 registros válidos = 87,5 %"]
        (TARGET/"VERIFICACION.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({"rows":8,"attendance_pct":report["metrics"]["asistencia_pct"],"files":list(manifest["files"]),"target":str(TARGET)},ensure_ascii=False))

if __name__=="__main__":main()
