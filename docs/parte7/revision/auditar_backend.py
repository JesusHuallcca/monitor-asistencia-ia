"""Diagnóstico LOCAL; bloquea MySQL/red y nunca ejecuta una migración.
P7_AUDIT_IMPORT_OVERLAY=1 prueba una propuesta, NO valida el producto sin corregir.
"""
import os, sys, socket, urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[3]
os.chdir(R)
sys.path[:0]=[str(R),str(R/'backend')]
os.environ.update(DB_HOST='invalid.test',DB_NAME='audit_tests_only',DB_USER='test',DB_PASSWORD='synthetic-not-a-credential',JWT_SECRET_KEY='audit-local-test-only-'*4,EMOSCAN_ENABLED='false')
os.environ.pop('GEMINI_API_KEY',None)
os.environ.pop('GEMINI_MODEL',None)
from cryptography.fernet import Fernet
os.environ['FACE_ENCRYPTION_KEY']=Fernet.generate_key().decode()
from sqlalchemy import event, Engine
@event.listens_for(Engine,'do_connect')
def deny_mysql(dialect, *args, **kwargs):
 if dialect.name not in {'sqlite'}:raise AssertionError('Solo SQLite permitido en la auditoria')
def no_download(*a,**kw):raise RuntimeError('Descargas deshabilitadas en auditoria')
urllib.request.urlretrieve=no_download
def audit(event,args):
 if event=='socket.connect':
  address=args[1]
  if isinstance(address,tuple) and address[0] not in {'127.0.0.1','::1','localhost'}:raise RuntimeError('Red externa bloqueada en auditoria')
sys.addaudithook(audit)
if os.environ.get('P7_AUDIT_IMPORT_OVERLAY')=='1':
 from segmentacion.experimental_expresiones import segmentacion_expresiones as correct
 import types
 adapter=types.ModuleType('segmentacion.segmentacion_kmeans')
 for name in ('DEFAULT_DATA','FEATURES','fit_segments'):setattr(adapter,name,getattr(correct,name))
 def prepare_students(raw,expression_seed=2026,samples=40):
  return correct.prepare_students(raw,expression_seed=expression_seed,samples=samples).assign(modalidad='principal_4_variables')
 adapter.prepare_students=prepare_students
 sys.modules['segmentacion.segmentacion_kmeans']=adapter
if __name__=='__main__':
 import pytest
 args=sys.argv[1:] or ['backend/tests','-q','-p','no:cacheprovider','--tb=no','--continue-on-collection-errors','--disable-warnings']
 raise SystemExit(pytest.main(args))
