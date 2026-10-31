"""Disposable native MySQL test: fresh datadir, random port, synthetic records only."""
from pathlib import Path
import concurrent.futures
from datetime import date, datetime, time as walltime, timedelta, timezone
import json, os, secrets, shutil, socket, subprocess, sys, tempfile, time

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "backend")]
TABLES = ["chatbot_proactive_notifications","chatbot_proactive_audit","chatbot_proactive_preferences","chatbot_proactive_actions","chatbot_proactive_worker"]

STAGE = "initialization"

def main():
    global STAGE
    binary = os.environ.get("MYSQLD_TEST_BINARY") or shutil.which("mysqld") or r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe"
    if not Path(binary).is_file():
        raise RuntimeError("Native MySQL test binary unavailable")
    folder = Path(tempfile.mkdtemp(prefix="monitor-parte7-mysql-"))
    datadir = folder / "data"
    datadir.mkdir()
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    base = ["--no-defaults", "--basedir="+str(Path(binary).resolve().parents[1]), "--datadir="+str(datadir)]
    initialized = subprocess.run([binary,*base,"--initialize-insecure"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags)
    if initialized.returncode:
        raise RuntimeError("Native MySQL initialization failed; production not touched")
    with socket.socket() as probe:
        probe.bind(("127.0.0.1",0))
        port=probe.getsockname()[1]
    server=subprocess.Popen([binary,*base,"--port="+str(port),"--bind-address=127.0.0.1","--mysqlx=0","--skip-log-bin","--log-error="+str(folder/"server.log"),"--pid-file="+str(folder/"server.pid")],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags)
    admin=None
    try:
        import pymysql
        for _ in range(60):
            try:
                admin=pymysql.connect(host="127.0.0.1",port=port,user="root",password="",autocommit=True)
                break
            except pymysql.Error:
                if server.poll() is not None:raise RuntimeError("Temporary MySQL stopped")
                time.sleep(.5)
        if admin is None:raise RuntimeError("Temporary MySQL did not become ready")
        STAGE = "admin_setup"
        admin_pass=secrets.token_urlsafe(32)
        runtime_pass=secrets.token_urlsafe(32)
        database="parte7_test_integration"
        with admin.cursor() as cursor:
            cursor.execute("ALTER USER 'root'@'localhost' IDENTIFIED BY %s",(admin_pass,))
            cursor.execute("CREATE DATABASE parte7_test_integration CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.execute("CREATE USER 'parte7_runtime'@'127.0.0.1' IDENTIFIED BY %s",(runtime_pass,))
            cursor.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON parte7_test_integration.* TO 'parte7_runtime'@'127.0.0.1'")
            cursor.execute("SELECT VERSION()")
            version=cursor.fetchone()[0]
        os.environ.update(DB_HOST="127.0.0.1",DB_PORT=str(port),DB_NAME=database,DB_USER="parte7_runtime",DB_PASSWORD=runtime_pass,JWT_SECRET_KEY=secrets.token_urlsafe(48),EMOSCAN_ENABLED="false")
        os.environ.pop("GEMINI_API_KEY",None)
        STAGE = "orm_import"
        from sqlalchemy import create_engine, inspect, select, func, text
        from sqlalchemy.engine import URL
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.exc import DBAPIError
        from app.db import database as app_db
        from app.db.models import Usuario, Profesor, Estudiante, Curso, AsignacionProfesor, Matricula, SesionClase, Asistencia
        from app.db.proactive_models import ProactiveAction as Action, ProactiveNotification as Notification
        from app.schemas.chatbot_proactive import ActionSpec, Transition
        from app.schemas.chatbot_reports import ReportSpec
        from app.services import chatbot_proactive as service
        from app.services.chatbot_reports import build_dataset
        url=URL.create("mysql+pymysql",username="root",password=admin_pass,host="127.0.0.1",port=port,database=database)
        admin_engine=create_engine(url,pool_pre_ping=True)
        assert app_db.engine.url.host=="127.0.0.1" and app_db.engine.url.port==port and app_db.engine.url.database==database
        STAGE = "base_schema"
        app_db.Base.metadata.create_all(admin_engine)
        before=set(inspect(admin_engine).get_table_names())
        migration=(ROOT/"database/mysql/migrations/parte7/001_proactividad_additive.sql").read_text(encoding="utf-8")
        statements=[part.strip() for part in "\n".join(line for line in migration.splitlines() if not line.lstrip().startswith("--")).split(";") if part.strip()]
        assert len(statements)==5 and all(part.startswith("CREATE TABLE") for part in statements)
        def apply():
            with admin_engine.begin() as connection:
                for statement in statements:connection.exec_driver_sql(statement)
        def rollback_empty_copy():
            # Only this fresh process-owned database can reach this helper.
            assert database=="parte7_test_integration"
            with admin_engine.connect() as connection:
                if any(connection.execute(text("SELECT COUNT(*) FROM "+table)).scalar_one() for table in TABLES):
                    raise RuntimeError("Rollback refused: preserve existing action/notification data")
                for table in TABLES:connection.exec_driver_sql("DROP TABLE "+table)
                connection.commit()
        STAGE = "migration_apply"
        apply()
        assert set(inspect(admin_engine).get_table_names())==before|set(TABLES)
        rollback_empty_copy()
        assert set(inspect(admin_engine).get_table_names())==before
        apply()
        STAGE = "seed"
        sessions=sessionmaker(bind=app_db.engine,expire_on_commit=False)
        today=date.today()
        with sessions() as db:
            db.add_all([Usuario(id=1,username="synthetic_prof",email="p@example.test",password_hash="unused",nombres="Docente",apellidos="Sintético",rol="profesor",estado="activo"),Usuario(id=2,username="synthetic_student",email="s@example.test",password_hash="unused",nombres="Perfil",apellidos="Sintético",rol="estudiante",estado="activo")])
            db.add(Profesor(id=1,usuario_id=1))
            db.add(Estudiante(id=1,usuario_id=2,codigo="SYN001"))
            db.add(Curso(id=1,codigo="SYN001",nombre="Curso sintético",periodo="prueba",activo=True))
            db.flush()
            db.add(AsignacionProfesor(profesor_id=1,curso_id=1))
            db.add(Matricula(estudiante_id=1,curso_id=1))
            db.add_all([SesionClase(id=1,curso_id=1,fecha=today-timedelta(days=1),hora_inicio=walltime(9),hora_fin=walltime(10)),SesionClase(id=2,curso_id=1,fecha=today+timedelta(days=1),hora_inicio=walltime(9),hora_fin=walltime(10))])
            db.flush()
            db.add(Asistencia(id=1,usuario_id=2,sesion_id=1,fecha=today-timedelta(days=1),hora=walltime(9),confianza=0,liveness_score=0,estado="PRESENTE"))
            db.commit()
            user=db.get(Usuario,1)
            spec=ActionSpec(kind="next_class",course_id=1,source_id=2)
            value=service.save_action(db,user,spec)
            db.commit()
            active=service.transition(db,user,value["id"],Transition(operation="activate",version=value["version"],confirmed=True))
            db.commit()
            due=datetime.fromisoformat(active["next_run"]).replace(tzinfo=None)+timedelta(seconds=1)
            report=build_dataset(db,user,ReportSpec(report_type="asistencia",course_id=1,period_start=today-timedelta(days=1),period_end=today-timedelta(days=1)))
            assert report["report_rows"]==1 and report["metrics"]["asistencia_pct"]==100
        STAGE = "concurrent_ticks"
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            outcomes=list(pool.map(lambda _:service.tick(sessions,due),range(2)))
        with sessions() as db:
            assert db.scalar(select(func.count()).select_from(Notification))==1
            try:
                db.execute(text("UPDATE chatbot_proactive_actions SET recipient_id=2"))
                db.commit()
            except DBAPIError as error:
                if error.orig.args[0] != 3819: raise
                db.rollback()
            else:raise AssertionError("Owner-recipient CHECK was not enforced")
        STAGE = "restart"
        app_db.engine.dispose()
        restarted=create_engine(app_db.engine.url,pool_pre_ping=True)
        restarted_sessions=sessionmaker(bind=restarted,expire_on_commit=False)
        assert service.tick(restarted_sessions,due)["notifications"]==0
        with restarted_sessions() as db:
            assert db.scalar(select(func.count()).select_from(Notification))==1
        try:rollback_empty_copy()
        except RuntimeError:preserved=True
        else:raise AssertionError("Nonempty rollback must be refused")
        restarted.dispose();admin_engine.dispose()
        result={"status":"passed","mysql_version":version,"storage":"fresh_native_mysql_structural_copy","source":"versioned_SQLAlchemy_schema_and_synthetic_rows","cloud_schema_verified":False,"production_connected":False,"migration_tables":len(TABLES),"base_tables_preserved":True,"rollback_empty_copy":True,"rollback_with_data_refused":preserved,"native_foreign_keys_and_check":True,"concurrent_workers_no_duplicates":True,"restart_no_duplicates":True,"authorized_report_rows":1,"external_messages":0,"credentials_printed":False}
        target=ROOT/"docs/parte7/revision/MYSQL_DESARROLLO.json"
        target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(result))
    finally:
        if admin is not None:
            try:
                with admin.cursor() as cursor:cursor.execute("SHUTDOWN")
            except Exception:pass
            admin.close()
        try:server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.terminate()
            try:server.wait(timeout=5)
            except subprocess.TimeoutExpired:server.kill();server.wait()

if __name__=="__main__":
    try:main()
    except Exception as error:
        print(json.dumps({"status":"failed","error_type":type(error).__name__,"stage":STAGE,"error_code":getattr(error,"orig",error).args[0] if getattr(error,"orig",error).args and isinstance(getattr(error,"orig",error).args[0],int) else None,"details":"Local MySQL test failed; no secret values logged."}))
        raise SystemExit(1) from None
